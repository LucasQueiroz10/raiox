"""Cenário simulado (números inventados, não são dados reais):

Carteira de R$ 4.000:
- R$ 1.000 direto no BANCO;
- R$ 3.000 num ETF: 40% VAREJO, 30% CHIPS, 20% SEMCLASSE, 5% caixa, 5% Tesouro.

Ações: BANCO 1.000 · VAREJO 1.200 · CHIPS 900 · SEMCLASSE 600 = 3.700.
"""

from datetime import date
from decimal import Decimal as D
from decimal import localcontext

from app.core.agregacao import NUCLEO, agregar
from app.core.classificacao import (
    Classificacao,
    Origem,
    ParticipacaoTema,
    TabelaClassificacao,
)
from app.core.composicao import Composicao, ItemComposicao, Posicao, TipoItem
from app.core.lookthrough import PRECISAO, abrir_carteira
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
        NUCLEO: D("1840"),  # núcleos: 660 (VAREJO) + 180 (CHIPS) + 1.000 (BANCO)
        None: D("600"),  # sem classificação (SEMCLASSE): não sabemos se é do tema
    }
    assert r.por_tema[IA].valor == D("1260")
    assert r.por_tema[IA].percentual == D("0.315")
    assert r.por_tema[NUCLEO].valor == D("1840")
    assert r.por_tema[None].valor == D("600")


def test_soma_por_tema_nao_passa_do_total_em_acoes():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    assert sum(f.valor for f in r.por_tema.values()) == D("3700")
    assert sum(f.valor for f in r.por_subtema.values()) == D("3700")


def test_tema_calculado_pelo_modelo_fica_preliminar():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    assert r.por_tema[IA].valor_preliminar == D("1260")
    assert r.por_subtema[(IA, "Nuvem")].valor_preliminar == D("420")


def test_cobertura_e_sobre_o_valor_em_acoes_dividida_por_selo():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    c = r.cobertura
    # Caixa e Tesouro (300) ficam fora: a base são os 3.700 em ações.
    assert c.total_acoes == D("3700")
    assert (c.confirmada, c.preliminar, c.sem_classificacao) == (
        D("2100"),  # VAREJO e CHIPS: setor de fonte oficial
        D("1000"),  # BANCO: setor do Wikidata
        D("600"),  # SEMCLASSE
    )
    with localcontext(prec=PRECISAO):
        assert c.percentual_confirmada == D(2100) / D(3700)
        assert c.percentual_classificada == D(3100) / D(3700)


def test_cobertura_sem_acoes_e_zero():
    assert agregar(abrir_carteira([], {}), tabela_simulada()).cobertura.percentual_classificada == 0


def lookthrough_com_derivativos():
    """ETF de R$ 1.000 com derivativos, crédito e posição vendida (números inventados)."""
    etf = Composicao(
        ETF,
        date(2026, 8, 31),
        "teste",
        (
            ItemComposicao(CHIPS, D("0.50"), TipoItem.ACAO),
            ItemComposicao(None, D("0.10"), TipoItem.DERIVATIVO, ativo_objeto_isin=CHIPS),
            ItemComposicao(None, D("0.02"), TipoItem.DERIVATIVO, ativo_objeto_isin=SEMCLASSE),
            ItemComposicao(None, D("0.05"), TipoItem.DERIVATIVO),
            ItemComposicao(isin("DEBENTURE"), D("0.10"), TipoItem.CREDITO, emissor_isin=VAREJO),
            ItemComposicao(BANCO, D("-0.05"), TipoItem.ACAO),
        ),
    )
    return abrir_carteira([Posicao(ETF, D("1000"), TipoItem.FUNDO)], {ETF: etf})


def test_derivativos_agrupados_pelo_setor_do_ativo_objeto():
    r = agregar(lookthrough_com_derivativos(), tabela_simulada())

    assert {s: f.valor for s, f in r.derivativos_por_setor.items()} == {
        "Tecnologia": D("100"),
        None: D("70"),  # ativo-objeto sem classificação (20) ou desconhecido (50)
    }


def test_credito_agrupado_pelo_setor_do_emissor():
    r = agregar(lookthrough_com_derivativos(), tabela_simulada())

    assert {s: f.valor for s, f in r.credito_por_setor.items()} == {"Varejo digital": D("100")}


def test_vendidos_agrupados_por_setor_sem_descontar_das_acoes():
    r = agregar(lookthrough_com_derivativos(), tabela_simulada())

    assert {s: f.valor for s, f in r.vendido_por_setor.items()} == {"Financeiro": D("-50")}
    assert "Financeiro" not in r.por_setor
    assert r.por_setor["Tecnologia"].valor == D("500")


def test_lista_de_empresas_maiores_primeiro_com_as_escondidas_marcadas():
    r = agregar(lookthrough_simulado(), tabela_simulada())

    assert [(e.isin, e.total, e.escondida) for e in r.empresas] == [
        (VAREJO, D("1200"), True),
        (BANCO, D("1000"), False),  # só direto
        (CHIPS, D("900"), True),
        (SEMCLASSE, D("600"), True),
    ]
    varejo = r.empresas[0]
    assert (varejo.setor, varejo.percentual, varejo.fundos) == ("Varejo digital", D("0.3"), {ETF})
    assert [t.subtema for t in varejo.temas] == ["Nuvem", "Modelos"]
    assert r.empresas[3].setor is None


def test_empresa_so_com_credito_ou_vendido_fica_fora_da_lista():
    r = agregar(lookthrough_com_derivativos(), tabela_simulada())

    assert [e.isin for e in r.empresas] == [CHIPS]
