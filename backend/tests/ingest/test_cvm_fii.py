"""Leitor do Informe Mensal de FII e a regra do tipo de cada FII (decisão de 13/10/2026)."""

from datetime import date

import pytest

from ingest.arquivos_cvm import LayoutInesperado
from ingest.cvm_fii import COLUNAS, TipoFII, ler_informes_fii
from tests.ficticios import cnpj, isin
from tests.ingest.fii_sintetico import EMAIL_DO_ADMINISTRADOR, AnoFII

FII = cnpj("FII")


def tipo(segmento: str = "Logística", **carteira: str):
    lido = ler_informes_fii([AnoFII().fundo(FII, segmento=segmento, **carteira).zip()])
    f = lido.fundos[FII]
    return f.tipo, f.segmento


@pytest.mark.parametrize(
    ("carteira", "esperado"),
    [
        ({"Direitos_Bens_Imoveis": "600", "CRI_CRA": "400"}, TipoFII.TIJOLO),
        # Participação em empresa dona de imóveis também é tijolo.
        ({"Cotas_Sociedades_Atividades_FII": "600", "FII": "400"}, TipoFII.TIJOLO),
        ({"CRI_CRA": "500", "LCI_LCA": "200", "Direitos_Bens_Imoveis": "300"}, TipoFII.PAPEL),
        ({"FII": "800", "CRI_CRA": "200"}, TipoFII.FUNDO_DE_FUNDOS),
        # Nenhum grupo com mais da metade: genérico.
        ({"Direitos_Bens_Imoveis": "400", "CRI_CRA": "300", "FII": "300"}, TipoFII.GENERICO),
        # Metade exata não basta: precisa ser mais da metade.
        ({"Direitos_Bens_Imoveis": "500", "CRI_CRA": "500"}, TipoFII.GENERICO),
        # O resto (ações, outros fundos) conta no total, mas não em nenhum grupo.
        ({"Direitos_Bens_Imoveis": "450", "Acoes": "550"}, TipoFII.GENERICO),
        ({}, TipoFII.GENERICO),  # carteira zerada
    ],
)
def test_o_grupo_com_mais_da_metade_do_investido_define_o_tipo(carteira, esperado):
    assert tipo(**carteira)[0] is esperado


@pytest.mark.parametrize(
    ("segmento", "esperado"),
    [
        ("Logística", "Logística"),
        ("Escritórios", "Escritórios"),
        ("Shoppings", "Shoppings"),
        ("Multicategoria", None),  # tijolo em vários segmentos
        ("Outros", None),
        ("", None),
    ],
)
def test_so_o_tijolo_leva_o_segmento_informado(segmento, esperado):
    assert tipo(segmento, Direitos_Bens_Imoveis="1000") == (TipoFII.TIJOLO, esperado)


@pytest.mark.parametrize("carteira", [{"CRI_CRA": "1000"}, {"FII": "1000"}, {"Acoes": "1000"}])
def test_papel_fundo_de_fundos_e_generico_nao_levam_segmento(carteira):
    assert tipo("Logística", **carteira)[1] is None


def test_fundo_sem_quadro_de_carteira_fica_generico():
    lido = ler_informes_fii([AnoFII().fundo(FII, carteira=False).zip()])

    assert (lido.fundos[FII].tipo, lido.fundos[FII].segmento) == (TipoFII.GENERICO, None)


def test_vale_o_informe_mais_recente_juntando_os_anos():
    antigo = AnoFII("2025").fundo(FII, data="2025-12-01", CRI_CRA="1000")
    novo = (
        AnoFII("2026")
        .fundo(FII, data="2026-08-01", versao="1", FII="1000")
        .fundo(FII, data="2026-08-01", versao="2", Direitos_Bens_Imoveis="1000", nome="NOVO")
        .fundo(FII, data="2026-07-01", versao="3", CRI_CRA="1000")
    )

    f = ler_informes_fii([antigo.zip(), novo.zip()]).fundos[FII]

    assert (f.tipo, f.nome, f.data_referencia) == (TipoFII.TIJOLO, "NOVO", date(2026, 8, 1))


def test_isin_valido_liga_o_ticker_ao_fundo_e_o_invalido_fica_de_fora():
    valido, invalido = cnpj("FII-VALIDO"), cnpj("FII-INVALIDO")
    digito_errado = isin("FII")[:11] + str((int(isin("FII")[11]) + 1) % 10)
    ano = AnoFII().fundo(valido, isin=isin("FII")).fundo(invalido, isin=digito_errado)

    lido = ler_informes_fii([ano.zip()])

    assert (lido.fundos[valido].isin, lido.fundos[invalido].isin) == (isin("FII"), None)


def test_contato_do_administrador_nunca_sai_do_leitor():
    lido = ler_informes_fii([AnoFII().fundo(FII, Direitos_Bens_Imoveis="1").zip()])

    assert EMAIL_DO_ADMINISTRADOR not in repr(lido)


def test_coluna_diferente_para_a_leitura():
    sem_cri = tuple(c for c in COLUNAS["ativo_passivo"] if c != "CRI_CRA")

    with pytest.raises(LayoutInesperado, match="CRI_CRA"):
        ler_informes_fii([AnoFII().fundo(FII).zip(colunas={"ativo_passivo": sem_cri})])


def test_pacote_sem_o_quadro_de_ativos_para_a_leitura():
    with pytest.raises(LayoutInesperado, match="inf_mensal_fii_ativo_passivo_2026.csv"):
        ler_informes_fii([AnoFII().fundo(FII).zip(sem=("ativo_passivo",))])
