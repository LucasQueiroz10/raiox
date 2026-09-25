"""Leitura dos dados de entrada da carteira (cadastro manual e CSVs)."""

import re
from datetime import date
from decimal import Decimal

_DATA_BR = re.compile(r"([0-9]{2})/([0-9]{2})/([0-9]{4})")
_DATA_ISO = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")

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
        # Sem repetir o texto: ele pode ser dado da carteira e acabar em um log.
        raise ValueError(f"número inválido para separador decimal {decimal!r}")
    milhar = "." if decimal == "," else ","
    return Decimal(limpo.replace(milhar, "").replace(decimal, "."))


def ler_data(texto: str) -> date:
    """Aceita dd/mm/aaaa ou aaaa-mm-dd; qualquer outro formato lança ValueError."""
    limpo = texto.strip()
    if m := _DATA_BR.fullmatch(limpo):
        dia, mes, ano = m.groups()
    elif m := _DATA_ISO.fullmatch(limpo):
        ano, mes, dia = m.groups()
    else:
        raise ValueError("data em formato não reconhecido (use dd/mm/aaaa ou aaaa-mm-dd)")
    return date(int(ano), int(mes), int(dia))
