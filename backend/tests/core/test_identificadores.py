import pytest

from app.core.identificadores import digito_verificador

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
