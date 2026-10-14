"""Do identificador da posição ao ativo_id (ADR 0005, seção 5), com uma identificação sintética."""

import pytest

from app.core.composicao import TipoItem
from app.core.traducao import AtivoIdentificado, TabelaIdentificacao, traduzir
from tests.ficticios import cnpj, isin_da_raiz

ACAO, FUNDO = TipoItem.ACAO, TipoItem.FUNDO
ON = isin_da_raiz("ZZAA", "ACNOR")  # ação com ISIN, ticker ZZAA3
PN = "B3:ZZAA4"  # ação que nenhum fundo tem: código interno da B3
ETF = f"CNPJ:{cnpj('ETF')}"
FII, ISIN_DO_FII = f"CNPJ:{cnpj('FII')}", isin_da_raiz("ZZFI", "CTF00")
# Dois FIIs com a mesma raiz no ISIN: pela raiz, não dá para saber qual é.
FII_B, FII_C = f"CNPJ:{cnpj('FII-B')}", f"CNPJ:{cnpj('FII-C')}"
ACAO_EUA = "US:ZZQ"

TABELA = TabelaIdentificacao.montar(
    [
        AtivoIdentificado(ON, ACAO, ticker_b3="ZZAA3", isin=ON),
        AtivoIdentificado(PN, ACAO, ticker_b3="ZZAA4"),
        AtivoIdentificado(ETF, FUNDO, ticker_b3="ZZTF11"),
        AtivoIdentificado(FII, FUNDO, isin=ISIN_DO_FII, fii=True),
        AtivoIdentificado(FII_B, FUNDO, isin=isin_da_raiz("ZZDU", "CTF00"), fii=True),
        AtivoIdentificado(FII_C, FUNDO, isin=isin_da_raiz("ZZDU", "CTF01"), fii=True),
        AtivoIdentificado(ACAO_EUA, ACAO, ticker_eua="ZZQ"),
    ]
)


@pytest.mark.parametrize(
    ("ticker", "ativo_id", "tipo"),
    [("ZZAA3", ON, ACAO), ("ZZAA4", PN, ACAO), ("ZZTF11", ETF, FUNDO)],
)
def test_ticker_da_b3_conhecido_vira_o_ativo_da_identificacao(ticker, ativo_id, tipo):
    assert traduzir("ticker_b3", ticker, ACAO, TABELA) == (ativo_id, tipo)


def test_fii_sem_ticker_conhecido_e_achado_pela_raiz_do_isin():
    # A raiz do ticker (4 primeiros caracteres) é o 3º ao 6º caractere do ISIN brasileiro.
    assert traduzir("ticker_b3", "ZZFI11", ACAO, TABELA) == (FII, FUNDO)


def test_raiz_de_mais_de_um_fii_nao_escolhe_nenhum():
    assert traduzir("ticker_b3", "ZZDU11", FUNDO, TABELA) == ("B3:ZZDU11", FUNDO)


def test_ticker_da_b3_desconhecido_vira_codigo_interno_com_o_tipo_declarado():
    assert traduzir("ticker_b3", "ZZZZ3", ACAO, TABELA) == ("B3:ZZZZ3", ACAO)
    assert traduzir("ticker_b3", "ZZZZ11", FUNDO, TABELA) == ("B3:ZZZZ11", FUNDO)


@pytest.mark.parametrize(
    ("isin", "esperado"),
    [
        (ON, (ON, ACAO)),  # ação: o próprio ISIN
        (ISIN_DO_FII, (FII, FUNDO)),  # FII: o CNPJ do fundo
    ],
)
def test_isin_conhecido_vira_o_ativo_da_identificacao(isin, esperado):
    assert traduzir("isin", isin, ACAO, TABELA) == esperado


def test_isin_desconhecido_fica_como_esta_com_o_tipo_declarado():
    desconhecido = isin_da_raiz("ZZXX", "UCITS")

    assert traduzir("isin", desconhecido, FUNDO, TABELA) == (desconhecido, FUNDO)


def test_ticker_americano_vira_us_mais_o_ticker():
    assert traduzir("ticker_eua", "ZZQ", FUNDO, TABELA) == (ACAO_EUA, ACAO)
    assert traduzir("ticker_eua", "ZZW.B", ACAO, TABELA) == ("US:ZZW.B", ACAO)


def test_cnpj_vira_o_fundo_pelo_cnpj():
    assert traduzir("cnpj", ETF.removeprefix("CNPJ:"), ACAO, TABELA) == (ETF, FUNDO)
    desconhecido = cnpj("DESCONHECIDO")
    assert traduzir("cnpj", desconhecido, FUNDO, TABELA) == (f"CNPJ:{desconhecido}", FUNDO)


def test_tipo_da_identificacao_prevalece_sobre_o_declarado():
    # Decisão do Lucas (14/10/2026): um FII ou ETF marcado como ação continua fundo, e uma ação
    # marcada como fundo continua ação.
    assert traduzir("ticker_b3", "ZZTF11", ACAO, TABELA)[1] is FUNDO
    assert traduzir("ticker_b3", "ZZAA3", FUNDO, TABELA)[1] is ACAO


def test_tabela_vazia_traduz_so_pelo_formato():
    vazia = TabelaIdentificacao.montar([])

    assert traduzir("ticker_b3", "ZZAA3", ACAO, vazia) == ("B3:ZZAA3", ACAO)
    assert traduzir("isin", ON, ACAO, vazia) == (ON, ACAO)


@pytest.mark.parametrize(
    "repetidos",
    [
        [
            AtivoIdentificado(PN, ACAO, ticker_b3="ZZAA3"),
            AtivoIdentificado(ON, ACAO, ticker_b3="ZZAA3"),
        ],
        [
            AtivoIdentificado("US:ZZQ", ACAO, ticker_eua="ZZQ"),
            AtivoIdentificado("US:ZZR", ACAO, ticker_eua="ZZQ"),
        ],
        [AtivoIdentificado(ON, ACAO, isin=ON), AtivoIdentificado(FII, FUNDO, isin=ON)],
    ],
    ids=["ticker_b3", "ticker_eua", "isin"],
)
def test_identificacao_com_identificador_repetido_e_recusada(repetidos):
    # O banco já garante um ativo por identificador em cada carga; a tabela confere de novo.
    with pytest.raises(ValueError, match="repetido"):
        TabelaIdentificacao.montar(repetidos)
