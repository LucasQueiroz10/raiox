from decimal import Decimal

import pytest

from app.core.importacao import ler_numero


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
