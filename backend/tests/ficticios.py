"""Dados sintéticos para os testes. O prefixo ZZ não é país: nenhum ISIN daqui existe."""

import hashlib

from app.core.identificadores import digito_verificador


def isin(nome: str) -> str:
    """ISIN fictício, válido e estável para cada nome, ex.: isin("FUNDOA").

    Nomes diferentes dão ISINs diferentes (hash), mesmo quando um é prefixo do outro.
    """
    corpo = "ZZ" + hashlib.sha256(nome.encode("utf-8")).hexdigest()[:9].upper()
    return corpo + digito_verificador(corpo)
