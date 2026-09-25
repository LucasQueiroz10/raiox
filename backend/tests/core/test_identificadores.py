import string

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from app.core.identificadores import digito_verificador, isin_valido, normalizar_isin

corpos_de_isin = st.builds(
    lambda pais, resto: pais + resto,
    st.text(string.ascii_uppercase, min_size=2, max_size=2),
    st.text(string.ascii_uppercase + string.digits, min_size=9, max_size=9),
)

# ISINs públicos de mercado (não são dados pessoais).
ISINS_CONHECIDOS = [
    "US0378331005",  # Apple
    "US5949181045",  # Microsoft
    "BRPETRACNPR6",  # Petrobras PN
    "BRVALEACNOR0",  # Vale ON
    "AU0000XVGZA3",  # exemplo com letras no meio
    "GB0002634946",  # BAE Systems
]


@pytest.mark.parametrize("isin", ISINS_CONHECIDOS)
def test_digito_verificador_reproduz_o_ultimo_caractere(isin):
    assert digito_verificador(isin[:11]) == isin[11]


@pytest.mark.parametrize("isin", ISINS_CONHECIDOS)
def test_isin_valido_aceita_isins_conhecidos(isin):
    assert isin_valido(isin)


@pytest.mark.parametrize(
    "texto",
    [
        "US0378331006",  # dígito verificador errado
        "US037833100",  # 11 caracteres
        "US03783310055",  # 13 caracteres
        "",
        "US03783310-5",  # caractere fora de A-Z e 0-9
        "1S0378331005",  # país com número
        "US037833100X",  # dígito verificador que não é número
        "us0378331005",  # minúsculas só são aceitas depois de normalizar
    ],
)
def test_isin_valido_recusa_formatos_invalidos(texto):
    assert not isin_valido(texto)


@pytest.mark.parametrize(
    "texto",
    ["US0378331005", " us0378331005 ", "\tUs0378331005\n", "us 0378 3310 05"],
)
def test_normalizar_isin_remove_espacos_e_poe_em_maiusculas(texto):
    assert normalizar_isin(texto) == "US0378331005"


@pytest.mark.parametrize("texto", ["US037833100", "US03783310-5", "1S0378331005", ""])
def test_normalizar_isin_recusa_formato_invalido(texto):
    with pytest.raises(ValueError, match="formato"):
        normalizar_isin(texto)


def test_normalizar_isin_recusa_digito_verificador_errado():
    with pytest.raises(ValueError, match="dígito verificador"):
        normalizar_isin("US0378331006")


@given(corpos_de_isin)
def test_corpo_mais_digito_calculado_forma_isin_valido(corpo):
    assert isin_valido(corpo + digito_verificador(corpo))


@given(corpos_de_isin, st.sampled_from(string.digits))
def test_qualquer_outro_digito_verificador_e_recusado(corpo, digito):
    assume(digito != digito_verificador(corpo))
    assert not isin_valido(corpo + digito)


@given(corpos_de_isin)
def test_normalizar_isin_e_idempotente(corpo):
    isin = corpo + digito_verificador(corpo)
    assert normalizar_isin(isin) == isin
    assert normalizar_isin(normalizar_isin(f" {isin.lower()} ")) == isin
