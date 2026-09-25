from datetime import date
from decimal import Decimal as D

from app.core.composicao import Categoria, Composicao, ItemComposicao, Posicao, TipoItem
from app.core.lookthrough import abrir_carteira
from tests.ficticios import isin

ACAO_A, ACAO_B, ACAO_C = isin("ACAOA"), isin("ACAOB"), isin("ACAOC")
ETF, FUNDO_DE_FUNDOS = isin("ETF"), isin("FOF")


def fundo(fundo_isin: str, *itens: tuple[str | None, str, TipoItem], **extra) -> Composicao:
    return Composicao(
        fundo_isin=fundo_isin,
        data_referencia=date(2026, 8, 31),
        fonte="teste",
        itens=tuple(ItemComposicao(i, D(p), t) for i, p, t in itens),
        **extra,
    )


def indexar(*composicoes: Composicao) -> dict[str, Composicao]:
    return {c.fundo_isin: c for c in composicoes}


ETF_60_40 = fundo(ETF, (ACAO_A, "0.6", TipoItem.ACAO), (ACAO_B, "0.4", TipoItem.ACAO))


def test_acao_direta_vai_inteira_para_a_empresa():
    r = abrir_carteira([Posicao(ACAO_A, D("1000"), TipoItem.ACAO)], {})

    assert r.total == D("1000")
    assert r.empresas[ACAO_A].direto == D("1000")
    assert r.empresas[ACAO_A].via_fundos == 0
    assert r.categorias[Categoria.ACOES] == D("1000")


def test_etf_divide_o_valor_pelos_pesos():
    r = abrir_carteira([Posicao(ETF, D("1000"), TipoItem.FUNDO)], indexar(ETF_60_40))

    assert r.empresas[ACAO_A].via_fundos == D("600")
    assert r.empresas[ACAO_B].via_fundos == D("400")
    assert r.empresas[ACAO_A].fundos == {ETF}
    assert r.categorias[Categoria.ACOES] == D("1000")


def test_mesma_empresa_direta_e_via_fundo_soma_separando_as_origens():
    r = abrir_carteira(
        [Posicao(ACAO_A, D("500"), TipoItem.ACAO), Posicao(ETF, D("1000"), TipoItem.FUNDO)],
        indexar(ETF_60_40),
    )

    a = r.empresas[ACAO_A]
    assert (a.direto, a.via_fundos, a.total) == (D("500"), D("600"), D("1100"))
    assert r.total == D("1500")


def test_fundo_de_fundos_abre_em_cadeia_e_guarda_o_fundo_da_carteira():
    fof = fundo(
        FUNDO_DE_FUNDOS,
        (ETF, "0.5", TipoItem.FUNDO),
        (ACAO_C, "0.5", TipoItem.ACAO),
    )

    r = abrir_carteira(
        [Posicao(FUNDO_DE_FUNDOS, D("1000"), TipoItem.FUNDO)], indexar(fof, ETF_60_40)
    )

    assert r.empresas[ACAO_A].via_fundos == D("300")
    assert r.empresas[ACAO_B].via_fundos == D("200")
    assert r.empresas[ACAO_C].via_fundos == D("500")
    # O fundo que a pessoa tem na carteira, não o intermediário.
    assert r.empresas[ACAO_A].fundos == {FUNDO_DE_FUNDOS}


def test_carteira_vazia():
    r = abrir_carteira([], {})

    assert r.total == 0
    assert r.empresas == {}
    assert all(v == 0 for v in r.categorias.values())


def fundo_completo() -> Composicao:
    return Composicao(
        fundo_isin=ETF,
        data_referencia=date(2026, 8, 31),
        fonte="teste",
        itens=(
            ItemComposicao(ACAO_A, D("0.50"), TipoItem.ACAO),
            ItemComposicao(ACAO_B, D("-0.02"), TipoItem.ACAO),
            ItemComposicao(None, D("0.05"), TipoItem.CAIXA),
            ItemComposicao(None, D("0.03"), TipoItem.DERIVATIVO, ativo_objeto_isin=ACAO_A),
            ItemComposicao(None, D("0.01"), TipoItem.DERIVATIVO),
            ItemComposicao(isin("DEBENTURE"), D("0.06"), TipoItem.CREDITO, emissor_isin=ACAO_C),
            ItemComposicao(isin("TESOURO"), D("0.20"), TipoItem.TITULO_PUBLICO),
            ItemComposicao(isin("OUTRO"), D("0.04"), TipoItem.OUTRO),
        ),
    )


def test_cada_tipo_vai_para_a_sua_categoria_sem_normalizar():
    r = abrir_carteira([Posicao(ETF, D("1000"), TipoItem.FUNDO)], indexar(fundo_completo()))

    assert r.categorias == {
        Categoria.ACOES: D("500"),
        Categoria.VENDIDO: D("-20"),
        Categoria.CAIXA: D("50"),
        Categoria.DERIVATIVOS: D("40"),
        Categoria.CREDITO: D("60"),
        Categoria.TITULOS_PUBLICOS: D("200"),
        Categoria.OUTROS: D("40"),
        Categoria.NAO_IDENTIFICADO: D("130"),  # 1000 - soma dos itens
        Categoria.NAO_ABERTO: D("0"),
    }
    assert sum(r.categorias.values()) == r.total


def test_posicao_vendida_nao_desconta_da_exposicao_comprada():
    r = abrir_carteira(
        [Posicao(ACAO_B, D("100"), TipoItem.ACAO), Posicao(ETF, D("1000"), TipoItem.FUNDO)],
        indexar(fundo_completo()),
    )

    b = r.empresas[ACAO_B]
    assert (b.direto, b.via_fundos, b.vendido) == (D("100"), D("0"), D("-20"))
    assert b.total == D("100")


def test_derivativos_ficam_marcados_pelo_ativo_objeto():
    r = abrir_carteira([Posicao(ETF, D("1000"), TipoItem.FUNDO)], indexar(fundo_completo()))

    assert r.derivativos_por_ativo_objeto == {ACAO_A: D("30"), None: D("10")}
    # O derivativo não soma na exposição em ações da empresa.
    assert r.empresas[ACAO_A].via_fundos == D("500")


def test_credito_fica_marcado_na_empresa_emissora():
    r = abrir_carteira([Posicao(ETF, D("1000"), TipoItem.FUNDO)], indexar(fundo_completo()))

    c = r.empresas[ACAO_C]
    assert (c.credito, c.total) == (D("60"), D("0"))
    assert c.fundos == {ETF}
