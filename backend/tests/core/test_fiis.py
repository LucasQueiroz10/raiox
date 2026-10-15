"""FIIs no raio-x (ADR 0008, etapa 4.3): o FII conhecido entra na categoria "fundos imobiliários",
pelo tipo da carteira que informa à CVM, em vez de "não aberto"."""

from datetime import date
from decimal import Decimal as D

from app.core.composicao import (
    Categoria,
    ClasseFii,
    Composicao,
    ItemComposicao,
    Posicao,
    TipoFII,
    TipoItem,
)
from app.core.lookthrough import Aviso, CodigoAviso, abrir_carteira
from tests.ficticios import cnpj, isin

ACAO = isin("FII-ACAO")
FUNDO = f"CNPJ:{cnpj('FII-FUNDO')}"
LOGISTICA, SHOPPING, PAPEL = (f"CNPJ:{cnpj(f'FII-{n}')}" for n in ("LOG", "SHOP", "PAPEL"))
OUTRO_LOGISTICA = f"CNPJ:{cnpj('FII-LOG-2')}"
TIJOLO_LOG = ClasseFii(TipoFII.TIJOLO, "Logística")
CLASSES = {
    LOGISTICA: TIJOLO_LOG,
    OUTRO_LOGISTICA: TIJOLO_LOG,
    SHOPPING: ClasseFii(TipoFII.TIJOLO, "Shoppings"),
    PAPEL: ClasseFii(TipoFII.PAPEL),
}


def posicao(ativo_id: str, valor: str) -> Posicao:
    return Posicao(ativo_id, D(valor), TipoItem.FUNDO)


def test_fii_direto_entra_na_categoria_pelo_tipo_e_sem_aviso():
    r = abrir_carteira([posicao(LOGISTICA, "1000")], {}, fiis=CLASSES)

    assert r.categorias[Categoria.FUNDOS_IMOBILIARIOS] == D("1000")
    assert r.categorias[Categoria.NAO_ABERTO] == 0
    assert r.fiis == {TIJOLO_LOG: D("1000")}
    assert r.avisos == set()


def test_fiis_da_mesma_classe_somam_e_os_outros_ficam_separados():
    carteira = [
        posicao(LOGISTICA, "300"),
        posicao(OUTRO_LOGISTICA, "200"),
        posicao(SHOPPING, "100"),
        posicao(PAPEL, "400"),
    ]

    r = abrir_carteira(carteira, {}, fiis=CLASSES)

    assert r.fiis == {
        TIJOLO_LOG: D("500"),
        ClasseFii(TipoFII.TIJOLO, "Shoppings"): D("100"),
        ClasseFii(TipoFII.PAPEL): D("400"),
    }
    assert r.categorias[Categoria.FUNDOS_IMOBILIARIOS] == D("1000")


def test_fii_dentro_de_fundo_entra_na_categoria_pelo_look_through():
    # Como as cotas de FII do bloco de cotas de fundos do CDA, que trazem o CNPJ do FII.
    fundo = Composicao(
        FUNDO,
        date(2026, 8, 31),
        "teste",
        (
            ItemComposicao(ACAO, D("0.6"), TipoItem.ACAO),
            ItemComposicao(PAPEL, D("0.4"), TipoItem.FUNDO),
        ),
    )

    r = abrir_carteira([posicao(FUNDO, "1000")], {FUNDO: fundo}, fiis=CLASSES)

    assert r.categorias[Categoria.FUNDOS_IMOBILIARIOS] == D("400")
    assert r.categorias[Categoria.ACOES] == D("600")
    assert r.fiis == {ClasseFii(TipoFII.PAPEL): D("400")}
    assert sum(r.categorias.values()) == r.total


def test_fii_desconhecido_continua_nao_aberto_com_aviso():
    desconhecido = f"CNPJ:{cnpj('FII-DESCONHECIDO')}"

    r = abrir_carteira([posicao(desconhecido, "1000")], {}, fiis=CLASSES)

    assert r.categorias[Categoria.NAO_ABERTO] == D("1000")
    assert r.categorias[Categoria.FUNDOS_IMOBILIARIOS] == 0
    assert r.avisos == {Aviso(CodigoAviso.FUNDO_SEM_COMPOSICAO, desconhecido)}


def test_fii_com_composicao_e_aberto_como_qualquer_fundo():
    # Se um dia o FII tiver composição, ela vale mais que o tipo.
    com_composicao = Composicao(
        LOGISTICA, date(2026, 8, 31), "teste", (ItemComposicao(ACAO, D("1"), TipoItem.ACAO),)
    )

    r = abrir_carteira([posicao(LOGISTICA, "1000")], {LOGISTICA: com_composicao}, fiis=CLASSES)

    assert r.categorias[Categoria.ACOES] == D("1000")
    assert r.fiis == {}
