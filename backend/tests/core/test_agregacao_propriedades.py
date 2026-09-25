from datetime import date
from decimal import Decimal as D
from decimal import localcontext

from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.agregacao import agregar
from app.core.classificacao import (
    Classificacao,
    Origem,
    ParticipacaoTema,
    TabelaClassificacao,
)
from app.core.composicao import Categoria, Composicao, ItemComposicao, Posicao, TipoItem
from app.core.lookthrough import PRECISAO, abrir_carteira
from tests.ficticios import isin

ACOES = [isin(f"PACAO{i}") for i in range(5)]
ETF = isin("PETF")
SETORES = ["Tecnologia", "Financeiro", "Varejo digital"]
SUBTEMAS = ["Nuvem", "Modelos", "Semicondutores", "Energia"]
TOLERANCIA = D("1e-30")

valores = st.decimals(min_value=D("0"), max_value=D("1000000"), places=2)
pesos_etf = st.decimals(min_value=D("-0.2"), max_value=D("0.6"), places=4)

itens_etf = st.one_of(
    st.builds(lambda i, p: ItemComposicao(i, p, TipoItem.ACAO), st.sampled_from(ACOES), pesos_etf),
    st.builds(
        lambda o, p: ItemComposicao(None, p, TipoItem.DERIVATIVO, ativo_objeto_isin=o),
        st.none() | st.sampled_from(ACOES),
        pesos_etf,
    ),
    st.builds(
        lambda e, p: ItemComposicao(isin("PDEB"), p, TipoItem.CREDITO, emissor_isin=e),
        st.sampled_from(ACOES),
        pesos_etf,
    ),
)

carteiras = st.tuples(
    st.lists(st.tuples(st.sampled_from(ACOES), valores), max_size=5),
    valores,
    st.lists(itens_etf, max_size=6),
)

temas = st.lists(
    st.builds(
        lambda s, p: ParticipacaoTema("Cadeia de IA", s, p),
        st.sampled_from(SUBTEMAS),
        st.decimals(min_value=D("0.01"), max_value=D("0.33"), places=2),
    ),
    max_size=3,
)

classificacoes = st.dictionaries(
    st.sampled_from(ACOES),
    st.tuples(st.sampled_from(SETORES), st.sampled_from(list(Origem)), temas),
)


def montar(carteira, tabela_bruta):
    diretas, valor_etf, itens = carteira
    posicoes = [Posicao(i, v, TipoItem.ACAO) for i, v in diretas]
    posicoes.append(Posicao(ETF, valor_etf, TipoItem.FUNDO))
    etf = Composicao(ETF, date(2026, 8, 31), "teste", tuple(itens))
    resultado = abrir_carteira(posicoes, {ETF: etf})
    tabela = TabelaClassificacao(
        "prop",
        {
            i: Classificacao(i, setor, temas=tuple(ts), setor_origem=origem)
            for i, (setor, origem, ts) in tabela_bruta.items()
        },
    )
    return resultado, agregar(resultado, tabela)


def soma(fatias):
    with localcontext(prec=PRECISAO):
        return sum((f.valor for f in fatias.values()), D(0))


@settings(deadline=None)
@given(carteiras, classificacoes)
def test_setor_tema_e_subtema_fecham_com_o_valor_em_acoes(carteira, tabela_bruta):
    resultado, r = montar(carteira, tabela_bruta)
    acoes = resultado.categorias[Categoria.ACOES]

    for fatias in (r.por_setor, r.por_tema, r.por_subtema):
        assert abs(soma(fatias) - acoes) < TOLERANCIA
    assert abs(r.cobertura.total_acoes - acoes) < TOLERANCIA


@settings(deadline=None)
@given(carteiras, classificacoes)
def test_derivativos_e_vendidos_por_setor_fecham_com_as_categorias(carteira, tabela_bruta):
    resultado, r = montar(carteira, tabela_bruta)

    derivativos = resultado.categorias[Categoria.DERIVATIVOS]
    vendido = resultado.categorias[Categoria.VENDIDO]
    assert abs(soma(r.derivativos_por_setor) - derivativos) < TOLERANCIA
    assert abs(soma(r.vendido_por_setor) - vendido) < TOLERANCIA


@settings(deadline=None)
@given(carteiras, classificacoes)
def test_cobertura_fica_entre_0_e_100_por_cento(carteira, tabela_bruta):
    _, r = montar(carteira, tabela_bruta)

    c = r.cobertura
    assert 0 <= c.percentual_classificada <= 1
    assert abs(c.confirmada + c.preliminar + c.sem_classificacao - c.total_acoes) < TOLERANCIA
