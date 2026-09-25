from datetime import date
from decimal import Decimal

import pytest

from app.core.importacao import ler_data, ler_numero


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("1.234,56", Decimal("1234.56")),
        ("1234,56", Decimal("1234.56")),
        ("1.234.567", Decimal("1234567")),
        ("1.234", Decimal("1234")),  # no formato BR, ponto é milhar
        ("0,5", Decimal("0.5")),
        ("-0,40", Decimal("-0.40")),
        ("  12,00 ", Decimal("12.00")),
        ("10", Decimal("10")),
    ],
)
def test_ler_numero_formato_brasileiro(texto, esperado):
    assert ler_numero(texto, decimal=",") == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("1,234.56", Decimal("1234.56")),
        ("1234.56", Decimal("1234.56")),
        ("1,234", Decimal("1234")),  # no formato US, vírgula é milhar
        ("0.000123", Decimal("0.000123")),
        ("-7.5", Decimal("-7.5")),
    ],
)
def test_ler_numero_formato_americano(texto, esperado):
    assert ler_numero(texto, decimal=".") == esperado


@pytest.mark.parametrize(
    ("texto", "decimal"),
    [
        ("1,234.56", ","),  # número americano lido como brasileiro
        ("1.234,56", "."),  # número brasileiro lido como americano
        ("12.34", ","),  # grupo de milhar com 2 dígitos
        ("", ","),
        ("-", ","),
        ("abc", ","),
        ("NaN", "."),
        ("Infinity", "."),
        ("1e5", "."),
        ("1,2,3", ","),
    ],
)
def test_ler_numero_recusa_texto_invalido_ou_do_formato_errado(texto, decimal):
    with pytest.raises(ValueError):
        ler_numero(texto, decimal=decimal)


def test_ler_numero_exige_separador_conhecido():
    with pytest.raises(ValueError):
        ler_numero("1", decimal=";")


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("24/09/2026", date(2026, 9, 24)),
        ("01/02/2026", date(2026, 2, 1)),  # dd/mm: 1º de fevereiro
        ("2026-09-24", date(2026, 9, 24)),
        (" 29/02/2024 ", date(2024, 2, 29)),
    ],
)
def test_ler_data(texto, esperado):
    assert ler_data(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "31/02/2026",  # dia que não existe
        "09/24/2026",  # formato americano mm/dd
        "24/09/26",  # ano com 2 dígitos
        "2026-09-24T10:00:00",
        "24-09-2026",
        "",
    ],
)
def test_ler_data_recusa_formato_invalido(texto):
    with pytest.raises(ValueError):
        ler_data(texto)


def test_erros_nao_repetem_o_valor_recebido():
    # O valor pode ser dado da carteira e a mensagem pode acabar em um log.
    with pytest.raises(ValueError) as erro_numero:
        ler_numero("98765,4x", decimal=",")
    with pytest.raises(ValueError) as erro_data:
        ler_data("98/76/5432x")
    assert "98765" not in str(erro_numero.value)
    assert "98/76" not in str(erro_data.value)
