"""Carga diária da PTAX no banco (ADR 0006; fecha a DT-1).

Uso, dentro de backend/, com RX_BANCO_URL do usuário rx_ingestao:
    python -m cargas.ptax              os últimos 15 dias (dias úteis às 13h30 e às 18h)
    python -m cargas.ptax --dias 60    uma janela maior (primeira carga)

1. Baixa da API PTAX do Banco Central (portal Olinda; matriz de dados, fonte 12, ODbL) a cotação de
   venda de fechamento do dólar de cada dia útil da janela, só na memória (`cargas/baixar.py`).
2. Compara com o que já está publicado e separa as datas novas e as que o Banco Central corrigiu.
   Sem nenhuma, nenhuma carga é aberta. A janela de 15 dias cobre os feriados e as correções.
3. Confere a variação: uma cotação que se afaste mais de 10% da do dia útil anterior trava a carga.
   É sinal de dado errado, que converteria todas as carteiras em dólar.
4. Grava as datas novas numa carga (`cargas/rotina.py`). A API lê a `ref.ptax_vigente`: em cada
   data, vale a cotação publicada por último, e a data de publicação é a data de consulta que o
   aviso do Banco Central mostra (`cambio.aviso_bcb` em docs/textos_telas.md).

Uma falha (download, formato da resposta, validação) deixa a carga "com_erro" e o comando termina
com erro, para o alerta (ADR 0007, seção 8). Se nem o registro der certo (banco fora do ar), o
comando termina com erro e mensagem curta, sem traceback, e quem avisa é o alerta de fonte sem carga
nova. Sem PTAX recente no banco, a API responde 503 nas carteiras em dólar.
"""

import argparse
import json
import logging
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

import psycopg

from app.core.calendario import hoje_em_brasilia
from app.core.cambio import ler_ptax_olinda
from app.dados.ptax import montar_url
from banco.preparar import url_libpq
from cargas.baixar import baixar
from cargas.rotina import (
    ErroDeValidacao,
    Gravar,
    expirar_paradas,
    motivo,
    publicar_carga,
    registrar_falha,
    trava,
)

PORTAL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/"
TIPO = "ptax"
FONTE = "Banco Central do Brasil – PTAX (API Olinda)"
JANELA_DIAS = 15
# Variação máxima entre dois dias úteis seguidos. A PTAX raramente anda mais de 5% num dia.
VARIACAO_MAXIMA = Decimal("0.10")

log = logging.getLogger("cargas.ptax")

type ObterCotacoes = Callable[[date, date], dict[date, Decimal]]


@dataclass(frozen=True)
class Relatorio:
    """O resultado da carga, para o log: contagens e datas (dado público)."""

    lidas: int
    gravadas: int
    carga_id: int | None  # None: nada mudou, nenhuma carga aberta
    ultima: date | None  # a cotação mais recente lida


def baixar_cotacoes(inicio: date, fim: date) -> dict[date, Decimal]:
    """As cotações de venda de fechamento entre as duas datas, pela API PTAX. A resposta fora do
    formato ou sem nenhuma cotação vira ErroDeValidacao (a carga não publica)."""
    conteudo = baixar(montar_url(inicio, fim), PORTAL)
    try:
        dados = json.loads(conteudo)
        if not isinstance(dados, dict):
            raise ValueError("resposta não é um objeto")
        cotacoes = ler_ptax_olinda(dados)
    except ValueError, KeyError, TypeError:
        raise ErroDeValidacao("resposta da API PTAX fora do formato esperado") from None
    if not cotacoes:
        raise ErroDeValidacao(
            f"a API PTAX não trouxe nenhuma cotação entre {inicio:%d/%m/%Y} e {fim:%d/%m/%Y}"
        )
    return cotacoes


def a_gravar(
    lidas: Mapping[date, Decimal], publicadas: Mapping[date, Decimal]
) -> dict[date, Decimal]:
    """As datas novas e as que o Banco Central corrigiu."""
    return {dia: valor for dia, valor in lidas.items() if publicadas.get(dia) != valor}


def conferir_variacao(novas: Mapping[date, Decimal], publicadas: Mapping[date, Decimal]) -> None:
    """Levanta ErroDeValidacao se uma cotação nova (ou o dia seguinte a uma corrigida) se afastar
    mais de VARIACAO_MAXIMA da cotação do dia útil anterior."""
    serie = dict(sorted({**publicadas, **novas}.items()))
    datas = list(serie)
    for anterior, dia in zip(datas, datas[1:], strict=False):
        if dia not in novas and anterior not in novas:
            continue
        variacao = abs(serie[dia] / serie[anterior] - 1)
        if variacao > VARIACAO_MAXIMA:
            raise ErroDeValidacao(
                f"a PTAX de {dia:%d/%m/%Y} varia {variacao:.1%} sobre a de {anterior:%d/%m/%Y};"
                f" o limite é {VARIACAO_MAXIMA:.0%}"
            )


def _publicadas(conexao: psycopg.Connection, desde: date) -> dict[date, Decimal]:
    return dict(
        conexao.execute(
            "SELECT data_cotacao, valor FROM ref.ptax_vigente WHERE data_cotacao >= %s", (desde,)
        ).fetchall()
    )


def _gravacao(novas: Mapping[date, Decimal]) -> Gravar:
    linhas = sorted(novas.items())

    def gravar(conexao: psycopg.Connection, carga_id: int) -> int:
        with conexao.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO ref.ptax (carga_id, data_cotacao, valor) VALUES (%s, %s, %s)",
                [(carga_id, dia, valor) for dia, valor in linhas],
            )
        return len(linhas)

    return gravar


def carregar(
    conexao: psycopg.Connection,
    hoje: date,
    obter: ObterCotacoes = baixar_cotacoes,
    dias: int = JANELA_DIAS,
) -> Relatorio:
    """Carrega a janela que termina hoje. `obter` busca as cotações (os testes simulam o Banco
    Central): chamada aqui dentro, para uma falha no download também deixar a carga "com_erro"."""
    inicio = hoje - timedelta(days=dias)
    try:
        lidas = obter(inicio, hoje)
        # Uma janela a mais para trás: a primeira data lida precisa da anterior para a conferência.
        publicadas = _publicadas(conexao, inicio - timedelta(days=JANELA_DIAS))
        novas = a_gravar(lidas, publicadas)
        conferir_variacao(novas, publicadas)
    except Exception as erro:
        registrar_falha(conexao, TIPO, FONTE, hoje, erro)
        raise
    carga_id = publicar_carga(conexao, TIPO, FONTE, max(novas), _gravacao(novas)) if novas else None
    return Relatorio(len(lidas), len(novas), carga_id, max(lidas) if lidas else None)


def main(argv: list[str] | None = None) -> int:
    """Devolve 0 se a carga publicou (ou nada mudou), 1 se falhou e 2 se faltou a configuração.
    Nenhuma falha sai com traceback: o log traz só o motivo (cargas/rotina.motivo)."""
    parser = argparse.ArgumentParser(
        prog="python -m cargas.ptax", description="Carga da PTAX do Banco Central."
    )
    parser.add_argument(
        "--dias", type=int, default=JANELA_DIAS, help=f"janela, em dias (padrão: {JANELA_DIAS})"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    url = os.environ.get("RX_BANCO_URL")
    if not url:
        log.error("defina RX_BANCO_URL com o usuário rx_ingestao")
        return 2
    try:
        with psycopg.connect(url_libpq(url), autocommit=True) as conexao, trava(conexao, TIPO):
            expirar_paradas(conexao, TIPO)
            r = carregar(conexao, hoje_em_brasilia(), dias=args.dias)
    except Exception as erro:
        # O mesmo motivo da carga (ref.carga.motivo_erro). Se nem a falha foi registrada (banco
        # fora do ar), quem avisa é o alerta de fonte sem carga nova (ADR 0007, seção 8).
        log.error("PTAX com erro (%s)", motivo(erro))
        return 1
    carga = f"carga {r.carga_id}" if r.carga_id else "nenhuma carga: nada mudou"
    log.info(
        "PTAX: %d cotações lidas (a última de %s), %d gravadas (%s)",
        r.lidas,
        r.ultima,
        r.gravadas,
        carga,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
