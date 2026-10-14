"""Carga do cadastro: identificação (empresas e ativos) e setor oficial (ADR 0008, etapa 4).

Uso, dentro de backend/, com RX_BANCO_URL do usuário rx_ingestao:
    python -m cargas.cadastro                 baixa as fontes do portal da CVM (toda segunda, 9h)
    python -m cargas.cadastro --pasta DIR     lê os zips já baixados em DIR (desenvolvimento)

Fontes, todas do portal de dados abertos da CVM (matriz de dados): o FCA dos 3 anos mais recentes,
o informe mensal de FII dos 2 anos mais recentes e o CDA dos 3 meses mais recentes, mais a curadoria
manual (`cargas/curadoria/`). Tudo só na memória: nenhum arquivo bruto é guardado. A montagem e as
regras de identificação estão em `cargas/identificacao.py`.

Publica duas cargas, cada uma uma foto completa (ADR 0006, seção 3), pela rotina comum
(`cargas/rotina.py`):

1. **identificação:** `ref.empresa` (companhias do FCA e da curadoria) e `ref.ativo` (ações pelo
   ISIN ou pelo código interno da B3, ETFs e FIIs pelo CNPJ);
2. **classificação:** `ref.classificacao`, com o setor de atividade de cada companhia (origem
   "oficial", aprovado: o código já trata a origem oficial como revisada).

As duas são publicadas em transações separadas. Se a classificação falhar depois de a identificação
publicar, a API passa a usar a identificação nova com a classificação anterior: as empresas novas
ficam sem setor (nunca com setor errado) até a carga seguinte. Aceito assim na revisão do PR #70; a
carga com erro dispara o alerta (ADR 0007, seção 8).

Antes de publicar, a carga confere se o número de empresas e de ativos não caiu mais de 20% em
relação à foto vigente (fonte incompleta) e faz a varredura de CPF nos nomes. Uma falha, também no
download das fontes, antes de haver o que gravar, deixa a carga "com_erro" e o comando termina com
erro, para o alerta (ADR 0007, seção 8). Se nem o registro der certo (banco fora do ar), o comando
termina com erro e mensagem curta, sem traceback, e quem avisa é o alerta de fonte sem carga nova.

DT-15: a classificação publicada tem só o setor oficial. Quando houver linhas manuais ou do IrRAE,
esta carga precisa levá-las adiante, porque cada versão da classificação é uma foto completa.
"""

import argparse
import io
import logging
import os
import re
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import IO

import psycopg

from banco.preparar import url_libpq
from cargas import cvm
from cargas.baixar import baixar
from cargas.identificacao import Identificacao, ler_curadoria, montar
from cargas.rotina import (
    ErroDeValidacao,
    Gravar,
    expirar_paradas,
    motivo,
    publicar_carga,
    registrar_falha,
    trava,
)
from cargas.validacao import conferir_sem_cpf
from ingest.arquivos_cvm import LayoutInesperado
from ingest.cvm_cda import ler_mes
from ingest.cvm_fca import ler_fca
from ingest.cvm_fii import ler_informes_fii

PASTA_CURADORIA = Path(__file__).resolve().parent / "curadoria"
PORTAL = "https://dados.cvm.gov.br/dados/"
PORTAL_FCA = f"{PORTAL}CIA_ABERTA/DOC/FCA/DADOS/"
PORTAL_FII = f"{PORTAL}FII/DOC/INF_MENSAL/DADOS/"
ANOS_DO_FCA = 3  # algumas companhias não entregam o FCA todo ano (ex.: o do ano corrente)
ANOS_DO_FII = 2  # no começo do ano, o informe do ano corrente ainda está quase vazio
MESES_DO_CDA = 3
FONTE_IDENTIFICACAO = "CVM (FCA, CDA e informe mensal de FII)"
FONTE_CLASSIFICACAO = "CVM (FCA)"
# Uma foto nova com bem menos empresas ou ativos que a vigente indica fonte incompleta.
QUEDA_MAXIMA = Decimal("0.2")

log = logging.getLogger("cargas.cadastro")


@dataclass(frozen=True)
class Fontes:
    """Os arquivos já obtidos (baixados ou lidos de uma pasta)."""

    fca: list[IO[bytes]]  # pacotes anuais do FCA
    cda: list[IO[bytes]]  # zips mensais do CDA, do mais recente para o mais antigo
    fii: list[IO[bytes]]  # pacotes anuais do informe mensal de FII
    curadoria: Path = PASTA_CURADORIA


@dataclass(frozen=True)
class Relatorio:
    """O resultado da carga, para o log: só contagens."""

    empresas: int
    ativos: Counter[str] = field(default_factory=Counter)  # por espécie (ação pelo ISIN etc.)
    setores: int = 0
    descartes: dict[str, int] = field(default_factory=dict)


def carregar_cadastro(conexao: psycopg.Connection, fontes: Fontes) -> Relatorio:
    """Lê as fontes, monta e publica a identificação e a classificação."""
    try:
        identificacao = montar(
            ler_fca(fontes.fca),
            [ler_mes(z) for z in fontes.cda],
            ler_informes_fii(fontes.fii),
            ler_curadoria(fontes.curadoria),
        )
    except Exception as erro:
        registrar_falha(conexao, "identificacao", FONTE_IDENTIFICACAO, None, erro)
        raise
    with trava(conexao, "identificacao"):
        expirar_paradas(conexao, "identificacao")
        publicar_carga(
            conexao,
            "identificacao",
            FONTE_IDENTIFICACAO,
            None,
            _gravar_identificacao(identificacao),
        )
    with trava(conexao, "classificacao"):
        expirar_paradas(conexao, "classificacao")
        publicar_carga(
            conexao,
            "classificacao",
            FONTE_CLASSIFICACAO,
            None,
            _gravar_classificacao(identificacao),
        )
    return Relatorio(
        empresas=len(identificacao.empresas),
        ativos=Counter(_especie(a.ativo_id, a.fii_tipo) for a in identificacao.ativos),
        setores=len(identificacao.setores),
        descartes=dict(identificacao.descartes),
    )


def _especie(ativo_id: str, fii_tipo: str | None) -> str:
    if ativo_id.startswith("B3:"):
        return "acao_pelo_codigo_interno"
    if ativo_id.startswith("CNPJ:"):
        return "fii" if fii_tipo else "etf_ou_outro_fundo"
    return "acao_pelo_isin"


def _conferir_queda(conexao: psycopg.Connection, visao: str, rotulo: str, novos: int) -> None:
    # A visão é uma das duas fixas abaixo, nunca entrada de fora.
    (vigentes,) = conexao.execute(f"SELECT count(*) FROM ref.{visao}").fetchone()  # noqa: S608
    if vigentes and novos < vigentes * (1 - QUEDA_MAXIMA):
        raise ErroDeValidacao(f"a foto nova tem {novos} {rotulo}; a vigente tem {vigentes}")


def _gravar_identificacao(identificacao: Identificacao) -> Gravar:
    empresas = [(e.empresa_id, e.nome, e.cnpj) for e in identificacao.empresas]
    ativos = [
        (a.ativo_id, a.tipo, a.empresa_id, a.ticker_b3, a.isin, a.nome, a.fii_tipo, a.fii_segmento)
        for a in identificacao.ativos
    ]
    colunas_empresa = ("empresa_id", "nome", "cnpj")
    colunas_ativo = (
        "ativo_id", "tipo", "empresa_id", "ticker_b3", "isin", "nome", "fii_tipo", "fii_segmento",
    )  # fmt: skip

    def gravar(conexao: psycopg.Connection, carga_id: int) -> int:
        _conferir_queda(conexao, "empresa_vigente", "empresas", len(empresas))
        _conferir_queda(conexao, "ativo_vigente", "ativos", len(ativos))
        conferir_sem_cpf(empresas, colunas_empresa, chave="empresa_id")
        conferir_sem_cpf(ativos, colunas_ativo, chave="ativo_id")
        # Direto nas tabelas definitivas: as validações já rodaram acima, e os domínios e gatilhos
        # do banco conferem cada linha (identificadores do ADR 0005, carga aberta do tipo certo).
        # As empresas vão antes: cada ação aponta para uma empresa da mesma carga.
        _copiar(conexao, "ref.empresa", colunas_empresa, carga_id, empresas)
        _copiar(conexao, "ref.ativo", colunas_ativo, carga_id, ativos)
        return len(empresas) + len(ativos)

    return gravar


def _gravar_classificacao(identificacao: Identificacao) -> Gravar:
    setores = [(s.empresa_id, s.setor, "oficial", "aprovado") for s in identificacao.setores]
    colunas = ("empresa_id", "setor", "setor_origem", "setor_status")

    def gravar(conexao: psycopg.Connection, carga_id: int) -> int:
        _copiar(conexao, "ref.classificacao", colunas, carga_id, setores)
        return len(setores)

    return gravar


def _copiar(
    conexao: psycopg.Connection,
    tabela: str,
    colunas: Sequence[str],
    carga_id: int,
    linhas: Sequence[tuple[object, ...]],
) -> None:
    comando = f"COPY {tabela} (carga_id, {', '.join(colunas)}) FROM STDIN"
    with conexao.cursor() as cursor, cursor.copy(comando) as copia:
        for linha in linhas:
            copia.write_row((carga_id, *linha))


# --- Obtenção das fontes ---


def _mais_recentes(indice: str, padrao: str, quantidade: int) -> list[str]:
    """Os `quantidade` arquivos mais recentes do índice do portal (o ano ou mês está no nome).
    Sem nenhum, o portal mudou ou está fora do ar: LayoutInesperado, com a mensagem no motivo."""
    nomes = sorted(set(re.findall(padrao, indice)), reverse=True)
    if not nomes:
        raise LayoutInesperado(f"nenhum arquivo {padrao} no índice do portal")
    return nomes[:quantidade]


def _baixar_ultimos(portal: str, padrao: str, quantidade: int) -> list[IO[bytes]]:
    indice = baixar(portal, PORTAL).decode("utf-8", errors="replace")
    return [
        io.BytesIO(baixar(f"{portal}{nome}", PORTAL))
        for nome in _mais_recentes(indice, padrao, quantidade)
    ]


def baixar_fontes() -> Fontes:
    """Baixa do portal da CVM os arquivos de cada fonte (só na memória)."""
    return Fontes(
        fca=_baixar_ultimos(PORTAL_FCA, r"fca_cia_aberta_\d{4}\.zip", ANOS_DO_FCA),
        cda=_baixar_ultimos(cvm.PORTAL, r"cda_fi_\d{6}\.zip", MESES_DO_CDA),
        fii=_baixar_ultimos(PORTAL_FII, r"inf_mensal_fii_\d{4}\.zip", ANOS_DO_FII),
    )


def ler_pasta(pasta: Path) -> Fontes:
    """Lê os zips já baixados numa pasta, com os nomes do portal (desenvolvimento)."""

    def abrir(padrao: str, quantidade: int) -> list[IO[bytes]]:
        caminhos = sorted(pasta.glob(padrao), key=lambda c: c.name, reverse=True)[:quantidade]
        return [io.BytesIO(c.read_bytes()) for c in caminhos]

    return Fontes(
        fca=abrir("fca_cia_aberta_????.zip", ANOS_DO_FCA),
        cda=abrir("cda_fi_??????.zip", MESES_DO_CDA),
        fii=abrir("inf_mensal_fii_????.zip", ANOS_DO_FII),
    )


def main(argv: list[str] | None = None) -> int:
    """Devolve 0 se as duas cargas publicaram, 1 se algo falhou e 2 se faltou a configuração.
    Nenhuma falha sai com traceback: o log traz só o motivo (cargas/rotina.motivo)."""
    parser = argparse.ArgumentParser(
        prog="python -m cargas.cadastro", description="Carga do cadastro (identificação e setor)."
    )
    parser.add_argument("--pasta", type=Path, help="pasta com os zips já baixados")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    url = os.environ.get("RX_BANCO_URL")
    if not url:
        log.error("defina RX_BANCO_URL com o usuário rx_ingestao")
        return 2
    try:
        with psycopg.connect(url_libpq(url), autocommit=True) as conexao:
            try:
                fontes = ler_pasta(args.pasta) if args.pasta else baixar_fontes()
            except Exception as erro:
                # Falha antes de haver o que gravar: fica registrada, para o histórico e o alerta
                # de carga com erro (ADR 0007, seção 8).
                registrar_falha(conexao, "identificacao", FONTE_IDENTIFICACAO, None, erro)
                raise
            relatorio = carregar_cadastro(conexao, fontes)
    except Exception as erro:
        # O mesmo motivo da carga (ref.carga.motivo_erro), sem valores das linhas. Se nem a falha
        # foi registrada (banco fora do ar), quem avisa é o alerta de fonte sem carga nova.
        log.error("cadastro com erro (%s)", motivo(erro))
        return 1
    log.info(
        "cadastro publicado: %d empresas, ativos %s, %d setores; descartes: %s",
        relatorio.empresas,
        dict(relatorio.ativos),
        relatorio.setores,
        relatorio.descartes,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
