"""Carga das composições da CVM (CDA) no banco (ADR 0008, etapa 3).

Uso, dentro de backend/, com RX_BANCO_URL do usuário rx_ingestao:
    python -m cargas.cvm                        os 3 meses mais recentes (de terça a sábado, às 9h)
    python -m cargas.cvm --pular 3 --meses 9    os 9 meses seguintes (uma vez por semana)
    python -m cargas.cvm --meses 12             a primeira carga
    python -m cargas.cvm --zip cda_fi_202608.zip    um zip já baixado (desenvolvimento)

Para cada mês:

1. Baixa o zip do portal de dados abertos da CVM, só na memória, e passa pelo leitor
   (`ingest/cvm_cda.py`), que traduz as linhas e descarta o CPF de emissor pessoa física.
2. Compara cada fundo com a última composição publicada do mesmo mês e separa os que mudaram. A CVM
   republica os meses recentes quase todo dia; regravar o mês inteiro (26 mil fundos) encheria o
   banco de cópias iguais (carga incremental, decisão de 12/10/2026). A composição vigente de cada
   fundo continua sendo a publicada por último no mês mais recente (visão ref.composicao_vigente).
   Um fundo que some de uma republicação continua com a composição publicada antes.
3. Confere se o mês não perdeu fundos demais em relação ao já publicado (arquivo incompleto).
4. Grava só os fundos que mudaram, numa carga (`cargas/rotina.py`), depois da varredura de CPF.
5. Registra no log o relatório do mês: fundos lidos, gravados e sem mudança, descartes do leitor e
   os fundos gravados cuja soma das linhas fica a mais de 1% do patrimônio (verificação a do M1).

Sem nenhuma mudança, nenhuma carga é aberta. Uma falha (download, formato do arquivo, validação)
deixa a carga do mês "com_erro"; os outros meses seguem, e o comando termina com erro para o alerta
disparar (ADR 0007, seção 8).

Ficam de fora até o PR 2.1 do ADR 0008, que cria o lugar delas no banco: a parte confidencial (até
lá, aparece como "não identificado") e os fundos sem composição utilizável.
"""

import argparse
import io
import logging
import os
import re
import sys
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import IO

import psycopg

from banco.preparar import url_libpq
from cargas.baixar import baixar
from cargas.rotina import (
    ErroDeValidacao,
    Gravar,
    expirar_paradas,
    publicar_carga,
    registrar_falha,
    trava,
)
from cargas.validacao import conferir_sem_cpf
from ingest.cvm_cda import FONTE, MesCDA, ler_mes

PORTAL = "https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/"
TIPO = "composicoes_cvm"
# Uma republicação pode ganhar fundos (quem entrega atrasado), mas não perder muitos de uma vez:
# acima disso, o arquivo provavelmente veio incompleto, e a carga não publica.
QUEDA_MAXIMA = Decimal("0.2")
# Verificação a do M1: soma das linhas de cada fundo contra o patrimônio.
TOLERANCIA_DA_SOMA = Decimal("0.01")

_ARQUIVO_DO_MES = re.compile(r"cda_fi_(\d{6})\.zip")
_COLUNAS_COMPOSICAO = ("fundo_id", "nome_fundo", "data_referencia", "patrimonio")
# Toda coluna que a assinatura compara (_assinatura_lida) precisa ser gravada: uma que faltasse
# faria o fundo parecer mudado a cada carga, e o incremental pararia sem dar erro.
_COLUNAS_ITEM = (
    "fundo_id", "ordem", "ativo_id", "empresa_id", "tipo", "valor", "peso", "emissor",
    "ativo_objeto",
)  # fmt: skip

log = logging.getLogger("cargas.cvm")

# O que se compara entre a composição lida e a publicada: data, patrimônio e os itens, na ordem.
type _Assinatura = tuple[date, Decimal, tuple[tuple[object, ...], ...]]


@dataclass(frozen=True)
class Relatorio:
    """O resultado da carga de um mês, para o log. Só contagens e CNPJs de fundos (dado público)."""

    mes: str
    fundos_no_arquivo: int
    gravados: int
    sem_mudanca: int
    carga_id: int | None  # None: nada mudou, nenhuma carga aberta
    fora_de_1_por_cento: list[str] = field(default_factory=list)
    descartes: dict[str, int] = field(default_factory=dict)


def meses_do_portal(indice: str) -> list[str]:
    """Os meses (AAAAMM) que o índice do portal oferece, do mais recente para o mais antigo."""
    meses = sorted(set(_ARQUIVO_DO_MES.findall(indice)), reverse=True)
    if not meses:
        raise ValueError("nenhum mês no índice do portal da CVM")
    return meses


def escolher_meses(meses: list[str], quantidade: int, pular: int = 0) -> list[str]:
    """Os `quantidade` meses depois dos `pular` mais recentes (`meses` em ordem decrescente)."""
    return meses[pular : pular + quantidade]


def mes_do_arquivo(caminho: str) -> str:
    """O mês (AAAAMM) pelo nome do zip, que segue o do portal (cda_fi_AAAAMM.zip)."""
    achado = _ARQUIVO_DO_MES.fullmatch(Path(caminho).name)
    if achado is None:
        raise ValueError("o zip precisa ter o nome do portal: cda_fi_AAAAMM.zip")
    return achado.group(1)


def _inicio_do_mes(mes: str) -> date:
    return date(int(mes[:4]), int(mes[4:]), 1)


def _inicio_do_mes_seguinte(inicio: date) -> date:
    return date(inicio.year + inicio.month // 12, inicio.month % 12 + 1, 1)


def _assinatura_lida(lido: MesCDA, fundo_id: str) -> _Assinatura:
    c = lido.composicoes[fundo_id]
    itens = tuple(
        (i.tipo.value, i.ativo_id, i.empresa_id, i.emissor, i.ativo_objeto, i.peso) for i in c.itens
    )
    return (c.data_referencia, lido.patrimonio[fundo_id], itens)


def _publicadas_do_mes(conexao: psycopg.Connection, inicio: date) -> dict[str, _Assinatura]:
    """A última composição publicada de cada fundo no mês, para comparar com a lida."""
    cabecalhos = conexao.execute(
        "SELECT DISTINCT ON (p.fundo_id) p.composicao_id, p.fundo_id, p.data_referencia,"
        " p.patrimonio"
        " FROM ref.composicao p JOIN ref.carga c ON c.carga_id = p.carga_id"
        " WHERE c.status = 'publicada' AND c.tipo = %s"
        " AND p.data_referencia >= %s AND p.data_referencia < %s"
        " ORDER BY p.fundo_id, c.publicada_em DESC, c.carga_id DESC",
        (TIPO, inicio, _inicio_do_mes_seguinte(inicio)),
    ).fetchall()
    itens: dict[int, list[tuple[object, ...]]] = defaultdict(list)
    linhas = conexao.execute(
        "SELECT composicao_id, tipo, ativo_id, empresa_id, emissor, ativo_objeto, peso"
        " FROM ref.composicao_item WHERE composicao_id = ANY(%s)"
        " ORDER BY composicao_id, ordem",
        ([c[0] for c in cabecalhos],),
    )
    for composicao_id, *item in linhas:
        itens[composicao_id].append(tuple(item))
    return {
        fundo_id: (data, patrimonio, tuple(itens[composicao_id]))
        for composicao_id, fundo_id, data, patrimonio in cabecalhos
    }


def _conferir_queda(lido: MesCDA, publicadas: dict[str, _Assinatura]) -> None:
    antes, agora = len(publicadas), len(lido.composicoes)
    if antes and agora < antes * (1 - QUEDA_MAXIMA):
        raise ErroDeValidacao(
            f"o mês veio com {agora} fundos; as cargas publicadas do mês tinham {antes}"
        )


def _gravacao(lido: MesCDA, fundos: list[str]) -> Gravar:
    """A função de gravação da carga (cargas/rotina.py) para os fundos que mudaram."""
    composicoes = [
        (f, lido.nomes[f], lido.composicoes[f].data_referencia, lido.patrimonio[f]) for f in fundos
    ]
    itens = [
        (f, ordem, i.ativo_id, i.empresa_id, i.tipo.value, valor, i.peso, i.emissor, i.ativo_objeto)
        for f in fundos
        for ordem, (i, valor) in enumerate(
            zip(lido.composicoes[f].itens, lido.valores[f], strict=True), start=1
        )
    ]

    def gravar(conexao: psycopg.Connection, carga_id: int) -> int:
        # Segunda barreira contra CPF (a primeira é o leitor), antes de qualquer gravação.
        conferir_sem_cpf(composicoes, _COLUNAS_COMPOSICAO)
        conferir_sem_cpf(itens, _COLUNAS_ITEM)
        # Preparação em tabelas temporárias da sessão (ADR 0006, seção 5): somem no fim da
        # transação, ninguém mais as vê, e o COPY é bem mais rápido que um INSERT por linha.
        conexao.execute(
            "CREATE TEMP TABLE prep_composicao (fundo_id text, nome_fundo text,"
            " data_referencia date, patrimonio numeric) ON COMMIT DROP"
        )
        conexao.execute(
            "CREATE TEMP TABLE prep_item (fundo_id text, ordem integer, ativo_id text,"
            " empresa_id text, tipo text, valor numeric, peso numeric, emissor text,"
            " ativo_objeto text)"
            " ON COMMIT DROP"
        )
        with conexao.cursor() as cursor:
            for tabela, colunas, linhas in (
                ("prep_composicao", _COLUNAS_COMPOSICAO, composicoes),
                ("prep_item", _COLUNAS_ITEM, itens),
            ):
                comando = f"COPY {tabela} ({', '.join(colunas)}) FROM STDIN"
                with cursor.copy(comando) as copia:
                    for linha in linhas:
                        copia.write_row(linha)
        # Nas tabelas definitivas, os domínios do banco conferem os identificadores (ADR 0005:
        # nenhum CUSIP, SEDOL ou ISIN de país fora da lista).
        conexao.execute(
            "INSERT INTO ref.composicao"
            " (carga_id, fundo_id, nome_fundo, data_referencia, moeda, patrimonio)"
            " SELECT %s, fundo_id, nome_fundo, data_referencia, 'BRL', patrimonio"
            " FROM prep_composicao",
            (carga_id,),
        )
        conexao.execute(
            "INSERT INTO ref.composicao_item"
            " (composicao_id, ordem, ativo_id, empresa_id, tipo, valor, peso, emissor,"
            " ativo_objeto)"
            " SELECT c.composicao_id, i.ordem, i.ativo_id, i.empresa_id, i.tipo, i.valor,"
            " i.peso, i.emissor, i.ativo_objeto"
            " FROM prep_item i JOIN ref.composicao c"
            " ON c.carga_id = %s AND c.fundo_id = i.fundo_id",
            (carga_id,),
        )
        return len(composicoes) + len(itens)

    return gravar


def carregar_mes(
    conexao: psycopg.Connection, mes: str, obter_zip: Callable[[], IO[bytes]]
) -> Relatorio:
    """Carrega um mês (AAAAMM). `obter_zip` baixa (ou abre) o zip: chamado aqui dentro, para uma
    falha no download também deixar a carga do mês "com_erro"."""
    inicio = _inicio_do_mes(mes)
    try:
        lido = ler_mes(obter_zip())
        publicadas = _publicadas_do_mes(conexao, inicio)
        _conferir_queda(lido, publicadas)
    except Exception as erro:
        registrar_falha(conexao, TIPO, FONTE, inicio, erro)
        raise
    mudaram = sorted(f for f in lido.composicoes if publicadas.get(f) != _assinatura_lida(lido, f))
    carga_id = None
    if mudaram:
        carga_id = publicar_carga(conexao, TIPO, FONTE, inicio, _gravacao(lido, mudaram))
    return Relatorio(
        mes=mes,
        fundos_no_arquivo=len(lido.composicoes),
        gravados=len(mudaram),
        sem_mudanca=len(lido.composicoes) - len(mudaram),
        carga_id=carga_id,
        fora_de_1_por_cento=[
            f for f in mudaram if abs(lido.soma_das_linhas[f] - 1) > TOLERANCIA_DA_SOMA
        ],
        descartes=dict(lido.descartes),
    )


def _baixar_mes(mes: str) -> IO[bytes]:
    return io.BytesIO(baixar(f"{PORTAL}cda_fi_{mes}.zip", PORTAL))


def _registrar(relatorio: Relatorio) -> None:
    r = relatorio
    carga = f"carga {r.carga_id}" if r.carga_id else "nenhuma carga: nada mudou"
    log.info(
        "mês %s: %d fundos no arquivo, %d gravados (%s), %d sem mudança; descartes do leitor: %s",
        r.mes,
        r.fundos_no_arquivo,
        r.gravados,
        carga,
        r.sem_mudanca,
        r.descartes,
    )
    if r.fora_de_1_por_cento:
        log.warning(
            "mês %s: %d fundos gravados com a soma das linhas a mais de 1%% do patrimônio: %s",
            r.mes,
            len(r.fora_de_1_por_cento),
            ", ".join(r.fora_de_1_por_cento),
        )


def main(argv: list[str] | None = None) -> int:
    """Devolve 0 se todos os meses carregaram (ou não mudaram), 1 se algum falhou e 2 se faltou a
    configuração."""
    parser = argparse.ArgumentParser(
        prog="python -m cargas.cvm", description="Carga das composições da CVM (CDA)."
    )
    parser.add_argument("--meses", type=int, default=3, help="quantos meses (padrão: 3)")
    parser.add_argument("--pular", type=int, default=0, help="quantos meses recentes pular")
    parser.add_argument("--zip", type=Path, help="zip local, com o nome do portal")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    url = os.environ.get("RX_BANCO_URL")
    if not url:
        log.error("defina RX_BANCO_URL com o usuário rx_ingestao")
        return 2
    falhou = False
    with psycopg.connect(url_libpq(url), autocommit=True) as conexao, trava(conexao, TIPO):
        expiradas = expirar_paradas(conexao, TIPO)
        if expiradas:
            log.warning("%d cargas paradas em carregando marcadas com erro", expiradas)
        if args.zip:
            conteudo = args.zip.read_bytes()
            tarefas = [(mes_do_arquivo(args.zip.name), lambda: io.BytesIO(conteudo))]
        else:
            indice = baixar(PORTAL, PORTAL).decode("utf-8", errors="replace")
            meses = escolher_meses(meses_do_portal(indice), args.meses, args.pular)
            tarefas = [(mes, partial(_baixar_mes, mes)) for mes in meses]
        for mes, obter_zip in tarefas:
            try:
                _registrar(carregar_mes(conexao, mes, obter_zip))
            except Exception as erro:
                # O motivo completo fica na carga (ref.carga.motivo_erro); aqui, só o resumo.
                log.error("mês %s: carga com erro (%s: %s)", mes, type(erro).__name__, erro)
                falhou = True
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
