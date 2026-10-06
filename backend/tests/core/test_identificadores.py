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

# ISINs fictícios. O dígito verificador de cada um foi calculado por outra implementação, fora
# do app e conferida contra ISINs reais, para este teste não conferir o código contra ele mesmo.
# Nos de tipo EUA, o dígito de controle do CUSIP está errado de propósito: não podem existir.
ISINS_DE_REFERENCIA = [
    "USZQ4X7K2W17",  # tipo EUA, com letras
    "USZQ4X7K2H40",  # tipo EUA, dígito verificador 0
    "BRZQXWACNPR1",  # tipo B3, PN
    "BRZQXWACNOR4",  # tipo B3, ON
    "AU0000ZQXWK9",  # letras no meio
]


@pytest.mark.parametrize("isin", ISINS_DE_REFERENCIA)
def test_digito_verificador_reproduz_o_ultimo_caractere(isin):
    assert digito_verificador(isin[:11]) == isin[11]


@pytest.mark.parametrize("isin", ISINS_DE_REFERENCIA)
def test_isin_valido_aceita_isins_de_referencia(isin):
    assert isin_valido(isin)


@pytest.mark.parametrize(
    "texto",
    [
        "USZQ4X7K2W18",  # dígito verificador errado
        "USZQ4X7K2W1",  # 11 caracteres
        "USZQ4X7K2W177",  # 13 caracteres
        "",
        "USZQ4X7K2W-7",  # caractere fora de A-Z e 0-9
        "1SZQ4X7K2W17",  # país com número
        "USZQ4X7K2W1X",  # dígito verificador que não é número
        "uszq4x7k2w17",  # minúsculas só são aceitas depois de normalizar
    ],
)
def test_isin_valido_recusa_formatos_invalidos(texto):
    assert not isin_valido(texto)


@pytest.mark.parametrize(
    "texto",
    ["USZQ4X7K2W17", " uszq4x7k2w17 ", "\tUszq4x7k2w17\n", "us zq4x 7k2w 17"],
)
def test_normalizar_isin_remove_espacos_e_poe_em_maiusculas(texto):
    assert normalizar_isin(texto) == "USZQ4X7K2W17"


@pytest.mark.parametrize("texto", ["USZQ4X7K2W1", "USZQ4X7K2W-7", "1SZQ4X7K2W17", ""])
def test_normalizar_isin_recusa_formato_invalido(texto):
    with pytest.raises(ValueError, match="formato"):
        normalizar_isin(texto)


def test_normalizar_isin_recusa_digito_verificador_errado():
    with pytest.raises(ValueError, match="dígito verificador"):
        normalizar_isin("USZQ4X7K2W18")


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


@pytest.mark.parametrize("texto", ["USZQ4X7K2W18", "USZQ4X7K2W-7"])
def test_normalizar_isin_nao_repete_o_valor_na_mensagem(texto):
    # O ISIN de uma posição é dado da carteira e a mensagem pode acabar em um log.
    with pytest.raises(ValueError) as erro:
        normalizar_isin(texto)
    assert "ZQ4X7K2W" not in str(erro.value)
