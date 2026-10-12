"""CNPJ numérico e alfanumérico (Receita Federal, CNPJs com letras desde julho de 2026)."""

import string

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from app.core.identificadores import cnpj_valido, digitos_verificadores_cnpj, normalizar_cnpj

corpos_de_cnpj = st.text(string.ascii_uppercase + string.digits, min_size=12, max_size=12)

# Os três primeiros são exemplos do manual e dos códigos de referência da Receita Federal. Os dois
# últimos são sintéticos: a ordem 0000 nunca é emitida (a matriz é 0001), então não podem existir.
# Os dígitos de todos foram conferidos com o código de referência da Receita, para este teste não
# conferir o código contra ele mesmo.
CNPJS_DE_REFERENCIA = [
    "12ABC34501DE35",
    "1345C3A5000106",
    "R55231B3000757",
    "11222333000009",  # sintético, só números (formato antigo)
    "ZZ998877000008",  # sintético, com letras
]


@pytest.mark.parametrize("cnpj", CNPJS_DE_REFERENCIA)
def test_digitos_verificadores_reproduzem_os_dois_ultimos(cnpj):
    assert digitos_verificadores_cnpj(cnpj[:12]) == cnpj[12:]


@pytest.mark.parametrize("cnpj", CNPJS_DE_REFERENCIA)
def test_cnpj_valido_aceita_os_de_referencia(cnpj):
    assert cnpj_valido(cnpj)


@pytest.mark.parametrize(
    "texto",
    [
        "R55231B3000700",  # dígito verificador errado (exemplo da Receita)
        "11222333000019",  # primeiro dígito verificador errado
        "1345c3A5000106",  # minúscula (exemplo da Receita): só é aceita depois de normalizar
        "112223330000A9",  # letra no dígito verificador
        "1122233300000",  # 13 caracteres
        "112223330000099",  # 15 caracteres
        "",
        "12.ABC.345/01DE-35",  # com máscara: só é aceito depois de normalizar
    ],
)
def test_cnpj_valido_recusa_formatos_invalidos(texto):
    assert not cnpj_valido(texto)


@pytest.mark.parametrize(
    "texto",
    ["12ABC34501DE35", "12.ABC.345/01DE-35", " 12.abc.345/01de-35 ", "12 ABC 345 01DE 35"],
)
def test_normalizar_cnpj_tira_a_mascara_e_poe_em_maiusculas(texto):
    assert normalizar_cnpj(texto) == "12ABC34501DE35"


def test_normalizar_cnpj_aceita_o_formato_antigo_com_mascara():
    assert normalizar_cnpj("11.222.333/0000-09") == "11222333000009"


@pytest.mark.parametrize("texto", ["1122233300000", "112223330000A9", "", "12ABC34501DE3_"])
def test_normalizar_cnpj_recusa_formato_invalido(texto):
    with pytest.raises(ValueError, match="formato"):
        normalizar_cnpj(texto)


def test_normalizar_cnpj_recusa_digito_verificador_errado():
    with pytest.raises(ValueError, match="dígito verificador"):
        normalizar_cnpj("R55231B3000700")


@given(corpos_de_cnpj)
def test_corpo_mais_digitos_calculados_forma_cnpj_valido(corpo):
    assert cnpj_valido(corpo + digitos_verificadores_cnpj(corpo))


@given(corpos_de_cnpj, st.text(string.digits, min_size=2, max_size=2))
def test_quaisquer_outros_digitos_verificadores_sao_recusados(corpo, digitos):
    assume(digitos != digitos_verificadores_cnpj(corpo))
    assert not cnpj_valido(corpo + digitos)


@given(corpos_de_cnpj)
def test_normalizar_cnpj_e_idempotente(corpo):
    cnpj = corpo + digitos_verificadores_cnpj(corpo)
    mascarado = f" {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]} ".lower()
    assert normalizar_cnpj(cnpj) == cnpj
    assert normalizar_cnpj(normalizar_cnpj(mascarado)) == cnpj


@pytest.mark.parametrize("texto", ["R55231B3000700", "R55231B30007_0"])
def test_normalizar_cnpj_nao_repete_o_valor_na_mensagem(texto):
    # O CNPJ de um fundo pode ser dado da carteira e a mensagem pode acabar em um log.
    with pytest.raises(ValueError) as erro:
        normalizar_cnpj(texto)
    assert "R55231B3" not in str(erro.value)
