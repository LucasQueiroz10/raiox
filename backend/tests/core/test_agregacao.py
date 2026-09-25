"""Cenário simulado (números inventados, não são dados reais):

Carteira de R$ 4.000:
- R$ 1.000 direto no BANCO;
- R$ 3.000 num ETF: 40% VAREJO, 30% CHIPS, 20% SEMCLASSE, 5% caixa, 5% Tesouro.

Ações: BANCO 1.000 · VAREJO 1.200 · CHIPS 900 · SEMCLASSE 600 = 3.700.
"""

from datetime import date
from decimal import Decimal as D

from app.core.agregacao import agregar
from app.core.classificacao import (
    Classificacao,
    Origem,
    ParticipacaoTema,
    TabelaClassificacao,
)
from app.core.composicao import Composicao, ItemComposicao, Posicao, TipoItem
from app.core.lookthrough import abrir_carteira
from tests.ficticios import isin

BANCO, VAREJO, CHIPS, SEMCLASSE = isin("BANCO"), isin("VAREJO"), isin("CHIPS"), isin("SEMCLASSE")
ETF = isin("ETF")
IA = "Cadeia de IA"


def lookthrough_simulado():
    etf = Composicao(
        ETF,
        date(2026, 8, 31),
        "teste",
        (
            ItemComposicao(VAREJO, D("0.40"), TipoItem.ACAO),
            ItemComposicao(CHIPS, D("0.30"), TipoItem.ACAO),
            ItemComposicao(SEMCLASSE, D("0.20"), TipoItem.ACAO),
            ItemComposicao(None, D("0.05"), TipoItem.CAIXA),
            ItemComposicao(isin("TESOURO"), D("0.05"), TipoItem.TITULO_PUBLICO),
        ),
    )
    return abrir_carteira(
        [Posicao(BANCO, D("1000"), TipoItem.ACAO), Posicao(ETF, D("3000"), TipoItem.FUNDO)],
        {ETF: etf},
    )


def tabela_simulada() -> TabelaClassificacao:
    return TabelaClassificacao(
        "teste-v1",
        {
            VAREJO: Classificacao(
                VAREJO,
                "Varejo digital",
                temas=(
                    ParticipacaoTema(IA, "Nuvem", D("0.35")),
                    ParticipacaoTema(IA, "Modelos", D("0.10")),
                ),
            ),
            CHIPS: Classificacao(
                CHIPS, "Tecnologia", temas=(ParticipacaoTema(IA, "Semicondutores", D("0.80")),)
            ),
            BANCO: Classificacao(BANCO, "Financeiro", setor_origem=Origem.WIKIDATA),
        },
    )


def test_soma_por_setor_com_percentual_sobre_o_total_da_carteira():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    assert r.total == D("4000")
    assert {s: f.valor for s, f in r.por_setor.items()} == {
        "Financeiro": D("1000"),
        "Varejo digital": D("1200"),
        "Tecnologia": D("900"),
        None: D("600"),  # sem classificação
    }
    assert r.por_setor["Varejo digital"].percentual == D("0.3")
    assert r.por_setor[None].percentual == D("0.15")


def test_setor_preliminar_fica_marcado():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    assert r.por_setor["Financeiro"].valor_preliminar == D("1000")  # veio do Wikidata
    assert r.por_setor["Tecnologia"].valor_preliminar == 0  # fonte oficial


def test_resultado_leva_a_versao_da_tabela():
    assert agregar(lookthrough_simulado(), tabela_simulada()).versao_classificacao == "teste-v1"


def test_carteira_vazia_nao_divide_por_zero():
    r = agregar(abrir_carteira([], {}), tabela_simulada())

    assert r.total == 0
    assert r.por_setor == {}


def test_valor_da_empresa_se_divide_pelos_pesos_dos_temas():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    # VAREJO 1.200: Nuvem 35% = 420, Modelos 10% = 120. CHIPS 900: Semicondutores 80% = 720.
    assert {s: f.valor for s, f in r.por_subtema.items()} == {
        (IA, "Nuvem"): D("420"),
        (IA, "Modelos"): D("120"),
        (IA, "Semicondutores"): D("720"),
        None: D("2440"),  # núcleos (660 + 180 + 1.000) e sem classificação (600)
    }
    assert r.por_tema[IA].valor == D("1260")
    assert r.por_tema[IA].percentual == D("0.315")
    assert r.por_tema[None].valor == D("2440")


def test_soma_por_tema_nao_passa_do_total_em_acoes():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    assert sum(f.valor for f in r.por_tema.values()) == D("3700")
    assert sum(f.valor for f in r.por_subtema.values()) == D("3700")


def test_tema_calculado_pelo_modelo_fica_preliminar():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    assert r.por_tema[IA].valor_preliminar == D("1260")
    assert r.por_subtema[(IA, "Nuvem")].valor_preliminar == D("420")
