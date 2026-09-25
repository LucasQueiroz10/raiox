"""Dados sintéticos para os testes. O prefixo ZZ não é país: nenhum ISIN daqui existe."""

from app.core.identificadores import digito_verificador


def isin(nome: str) -> str:
    """ISIN fictício e válido a partir de um nome curto, ex.: isin("FUNDOA")."""
    corpo = "ZZ" + nome.upper().ljust(9, "0")[:9]
    return corpo + digito_verificador(corpo)
