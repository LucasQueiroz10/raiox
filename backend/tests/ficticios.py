"""Dados sintéticos para os testes. O prefixo ZZ não é país: nenhum ISIN daqui existe."""

import hashlib

from app.core.identificadores import digito_verificador, digitos_verificadores_cnpj


def isin(nome: str) -> str:
    """ISIN fictício, válido e estável para cada nome, ex.: isin("FUNDOA").

    Nomes diferentes dão ISINs diferentes (hash), mesmo quando um é prefixo do outro.
    """
    corpo = "ZZ" + hashlib.sha256(nome.encode("utf-8")).hexdigest()[:9].upper()
    return corpo + digito_verificador(corpo)


def isin_da_raiz(raiz: str, resto: str = "ACNOR") -> str:
    """ISIN fictício (prefixo ZZ) com a raiz de 4 caracteres escolhida, ex.: isin_da_raiz("ZZAA")
    tem a mesma raiz que o ticker ZZAA3 (a raiz é o código do emissor na B3)."""
    corpo = "ZZ" + raiz + resto
    return corpo + digito_verificador(corpo)


def cnpj(nome: str) -> str:
    """CNPJ alfanumérico fictício, válido e estável para cada nome, sem máscara, ex.: cnpj("ETF").

    Começa com ZZ e usa letras, como os CNPJs sintéticos dos testes com banco.
    """
    corpo = "ZZ" + hashlib.sha256(nome.encode("utf-8")).hexdigest()[:10].upper()
    return corpo + digitos_verificadores_cnpj(corpo)
