"""Leitura dos dados de entrada da carteira (cadastro manual e CSVs)."""

import re
from decimal import Decimal

# Separador decimal -> formato aceito. Milhar só em grupos de 3 dígitos.
_FORMATOS_NUMERO = {
    ",": re.compile(r"-?(?:[0-9]{1,3}(?:\.[0-9]{3})+|[0-9]+)(?:,[0-9]+)?"),
    ".": re.compile(r"-?(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"),
}


def ler_numero(texto: str, *, decimal: str) -> Decimal:
    """Converte texto em Decimal; o separador decimal da fonte é obrigatório.

    Com decimal="," (B3), "1.234,56" vira 1234.56. Com decimal="." (EUA), "1,234.56".
    Texto em outro formato lança ValueError, em vez de ser lido com outro valor.
    """
    formato = _FORMATOS_NUMERO.get(decimal)
    if formato is None:
        raise ValueError(f"separador decimal desconhecido: {decimal!r}")
    limpo = "".join(texto.split())
    if formato.fullmatch(limpo) is None:
        raise ValueError(f"número inválido para separador decimal {decimal!r}: {texto!r}")
    milhar = "." if decimal == "," else ","
    return Decimal(limpo.replace(milhar, "").replace(decimal, "."))
