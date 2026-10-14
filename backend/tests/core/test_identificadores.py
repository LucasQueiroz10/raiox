import string

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from app.core.identificadores import (
    IsinForaDaLista,
    digito_verificador,
    isin_valido,
    normalizar_isin,
    normalizar_isin_permitido,
    normalizar_ticker_b3,
    normalizar_ticker_eua,
)

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


# --- Entrada por identificador (ADR 0005, seção 5) ---

US_FICTICIO = "USZQ4X7K2W17"  # ISIN válido e fictício, de país fora da lista permitida


def test_isin_permitido_aceita_os_paises_da_lista():
    from tests.ficticios import isin

    assert normalizar_isin_permitido(f" {isin('PERMITIDO').lower()} ") == isin("PERMITIDO")


def test_isin_de_pais_fora_da_lista_pede_o_ticker_sem_repetir_o_valor():
    with pytest.raises(IsinForaDaLista, match="envie o ticker") as erro:
        normalizar_isin_permitido(US_FICTICIO)

    assert US_FICTICIO not in str(erro.value)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("ZZAA3", "ZZAA3"),
        (" zzaa4 ", "ZZAA4"),
        ("ZZTF11", "ZZTF11"),
        ("Z3ZA3", "Z3ZA3"),  # raiz com número no meio, como B3SA3
        ("ZZAA4F", "ZZAA4"),  # mercado fracionário: a mesma ação
        ("zztf11f", "ZZTF11"),
    ],
)
def test_ticker_b3_normalizado_e_sem_o_f_do_fracionario(texto, esperado):
    assert normalizar_ticker_b3(texto) == esperado


@pytest.mark.parametrize(
    "texto", ["ZZAA", "ZZAA123", "1ZAA3", "ZZAAF", "ZZAA3FF", "ZZ-A3", "ZZAA3G", ""]
)
def test_ticker_b3_fora_do_formato_e_recusado_sem_repetir_o_valor(texto):
    with pytest.raises(ValueError, match="ticker da B3") as erro:
        normalizar_ticker_b3(texto)

    assert not texto or texto not in str(erro.value)


@pytest.mark.parametrize(
    ("texto", "esperado"), [("ZZQ", "ZZQ"), (" zzq.b ", "ZZQ.B"), ("Z", "Z"), ("ZZQQQ", "ZZQQQ")]
)
def test_ticker_americano_normalizado(texto, esperado):
    assert normalizar_ticker_eua(texto) == esperado


@pytest.mark.parametrize("texto", ["ZZQQQQ", "ZZQ.BB", "ZZ1", "ZZQ-B", ""])
def test_ticker_americano_fora_do_formato_e_recusado(texto):
    with pytest.raises(ValueError, match="ticker americano"):
        normalizar_ticker_eua(texto)
