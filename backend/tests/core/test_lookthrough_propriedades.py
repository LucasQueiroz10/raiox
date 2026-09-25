from datetime import date
from decimal import Decimal as D
from decimal import localcontext

from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.composicao import Categoria, Composicao, ItemComposicao, Posicao, TipoItem
from app.core.lookthrough import PRECISAO, abrir_carteira
from tests.ficticios import isin

FUNDOS = [isin(f"HFUNDO{i}") for i in range(4)]
ACOES = [isin(f"HACAO{i}") for i in range(3)]
SEM_COMPOSICAO = isin("HSEMDADOS")

pesos = st.decimals(min_value=D("-0.5"), max_value=D("1.5"), places=4)
valores = st.decimals(min_value=D("0"), max_value=D("1000000"), places=2)

itens = st.one_of(
    st.builds(lambda i, p: ItemComposicao(i, p, TipoItem.FUNDO), st.sampled_from(FUNDOS), pesos),
    st.builds(lambda i, p: ItemComposicao(i, p, TipoItem.ACAO), st.sampled_from(ACOES), pesos),
    st.builds(
        lambda t, p, o: ItemComposicao(None, p, t, ativo_objeto_isin=o, emissor_isin=o),
        st.sampled_from([t for t in TipoItem if t not in (TipoItem.FUNDO, TipoItem.ACAO)]),
        pesos,
        st.none() | st.sampled_from(ACOES),
    ),
)

composicoes = st.fixed_dictionaries(
    {
        f: st.builds(
            lambda it, f=f: Composicao(f, date(2026, 8, 31), "teste", tuple(it)),
            st.lists(itens, max_size=5),
        )
        for f in FUNDOS
    }
)

posicoes = st.lists(
    st.one_of(
        st.builds(lambda i, v: Posicao(i, v, TipoItem.FUNDO), st.sampled_from(FUNDOS), valores),
        st.builds(lambda i, v: Posicao(i, v, TipoItem.ACAO), st.sampled_from(ACOES), valores),
        st.builds(lambda v: Posicao(SEM_COMPOSICAO, v, TipoItem.FUNDO), valores),
    ),
    max_size=4,
)


@settings(deadline=None)
@given(posicoes, composicoes)
def test_o_valor_da_carteira_sempre_se_conserva(carteira, fundos):
    r = abrir_carteira(carteira, fundos, max_passos=5000)

    assert abs(sum(r.categorias.values()) - r.total) < D("1e-20")


@settings(deadline=None)
@given(posicoes, composicoes)
def test_categorias_de_acoes_batem_com_as_empresas(carteira, fundos):
    r = abrir_carteira(carteira, fundos, max_passos=5000)

    with localcontext(prec=PRECISAO):  # mesma precisão do look-through
        acoes = sum((e.total for e in r.empresas.values()), D(0))
        vendido = sum((e.vendido for e in r.empresas.values()), D(0))
    assert r.categorias[Categoria.ACOES] == acoes
    assert r.categorias[Categoria.VENDIDO] == vendido
