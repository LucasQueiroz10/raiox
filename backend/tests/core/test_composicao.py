from datetime import date
from decimal import Decimal as D

from app.core.composicao import Categoria, Composicao, ItemComposicao, TipoItem
from tests.ficticios import isin


def composicao(*itens: ItemComposicao) -> Composicao:
    return Composicao(
        fundo_isin=isin("FUNDO"),
        data_referencia=date(2026, 8, 31),
        fonte="teste",
        itens=itens,
    )


def test_pesos_por_categoria_separa_cada_tipo_e_o_nao_identificado():
    c = composicao(
        ItemComposicao(isin("ACAOA"), D("0.50"), TipoItem.ACAO),
        ItemComposicao(isin("ACAOB"), D("-0.02"), TipoItem.ACAO),  # vendida a descoberto
        ItemComposicao(isin("OUTROFUNDO"), D("0.20"), TipoItem.FUNDO),
        ItemComposicao(None, D("0.05"), TipoItem.CAIXA),
        ItemComposicao(None, D("0.03"), TipoItem.DERIVATIVO, ativo_objeto_isin=isin("ACAOA")),
        ItemComposicao(isin("DEBENTURE"), D("0.06"), TipoItem.CREDITO),
        ItemComposicao(isin("TESOURO"), D("0.04"), TipoItem.TITULO_PUBLICO),
        ItemComposicao(isin("OUTRO"), D("0.01"), TipoItem.OUTRO),
    )

    assert c.pesos_por_categoria() == {
        Categoria.ACOES: D("0.50"),
        Categoria.VENDIDO: D("-0.02"),
        Categoria.FUNDOS: D("0.20"),
        Categoria.CAIXA: D("0.05"),
        Categoria.DERIVATIVOS: D("0.03"),
        Categoria.CREDITO: D("0.06"),
        Categoria.TITULOS_PUBLICOS: D("0.04"),
        Categoria.OUTROS: D("0.01"),
        Categoria.NAO_IDENTIFICADO: D("0.13"),  # 1 - soma de tudo acima
    }


def test_pesos_por_categoria_nao_normaliza():
    c = composicao(ItemComposicao(isin("ACAOA"), D("0.97"), TipoItem.ACAO))

    pesos = c.pesos_por_categoria()

    assert pesos[Categoria.ACOES] == D("0.97")
    assert pesos[Categoria.NAO_IDENTIFICADO] == D("0.03")


def test_pesos_acima_de_100_por_cento_deixam_nao_identificado_negativo():
    c = composicao(ItemComposicao(isin("ACAOA"), D("1.02"), TipoItem.ACAO))

    assert c.pesos_por_categoria()[Categoria.NAO_IDENTIFICADO] == D("-0.02")
