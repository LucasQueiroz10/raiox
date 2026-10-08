"""Identificadores com dígito verificador: ISIN e CNPJ (ADR 0005)."""

import re

# 2 letras de país (ou prefixo como XS), 9 caracteres alfanuméricos e 1 dígito verificador.
_FORMATO_ISIN = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")


def digito_verificador(corpo: str) -> str:
    """Calcula o 12º caractere do ISIN a partir dos 11 primeiros.

    Letras viram números (A=10 ... Z=35) e o resultado passa pelo algoritmo de Luhn.
    """
    digitos = "".join(str(int(c, 36)) for c in corpo)
    soma = 0
    # Da direita para a esquerda, dobra o 1º, o 3º, o 5º...
    # (o dígito verificador ainda não está na sequência).
    for posicao, c in enumerate(reversed(digitos)):
        n = int(c)
        if posicao % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        soma += n
    return str((10 - soma % 10) % 10)


def isin_valido(texto: str) -> bool:
    """Diz se o texto já é um ISIN válido (formato e dígito). Não normaliza."""
    return (
        _FORMATO_ISIN.fullmatch(texto) is not None and digito_verificador(texto[:11]) == texto[11]
    )


def normalizar_isin(texto: str) -> str:
    """Remove espaços, põe em maiúsculas e devolve o ISIN; lança ValueError se for inválido."""
    isin = "".join(texto.split()).upper()
    # Sem repetir o ISIN: ele pode ser dado da carteira e acabar em um log.
    if _FORMATO_ISIN.fullmatch(isin) is None:
        raise ValueError("ISIN com formato inválido")
    if digito_verificador(isin[:11]) != isin[11]:
        raise ValueError("ISIN com dígito verificador inválido")
    return isin


# CNPJ: 12 caracteres (raiz e ordem) e 2 dígitos verificadores. Desde julho de 2026 a Receita
# Federal emite CNPJs novos com letras maiúsculas nos 12 primeiros; os só com números continuam
# valendo. Os dígitos verificadores são sempre números.
_FORMATO_CNPJ = re.compile(r"[A-Z0-9]{12}[0-9]{2}")
_PESOS_CNPJ = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_MASCARA_CNPJ = str.maketrans("", "", "./-")


def _digito_cnpj(texto: str) -> str:
    # Cada caractere vale o código ASCII menos 48: os números valem 0 a 9, "A" vale 17 ... "Z" 42.
    soma = sum((ord(c) - 48) * p for c, p in zip(texto, _PESOS_CNPJ[-len(texto) :], strict=True))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def digitos_verificadores_cnpj(corpo: str) -> str:
    """Calcula os 2 dígitos verificadores a partir dos 12 primeiros caracteres (módulo 11, regra
    da Receita Federal que vale para o CNPJ numérico e para o alfanumérico)."""
    primeiro = _digito_cnpj(corpo)
    return primeiro + _digito_cnpj(corpo + primeiro)


def cnpj_valido(texto: str) -> bool:
    """Diz se o texto já é um CNPJ válido, sem máscara e em maiúsculas. Não normaliza."""
    return (
        _FORMATO_CNPJ.fullmatch(texto) is not None
        and digitos_verificadores_cnpj(texto[:12]) == texto[12:]
    )


def normalizar_cnpj(texto: str) -> str:
    """Tira a máscara (pontos, barra e traço) e os espaços, põe em maiúsculas e devolve os 14
    caracteres; lança ValueError se for inválido."""
    cnpj = "".join(texto.translate(_MASCARA_CNPJ).split()).upper()
    # Sem repetir o CNPJ: ele pode ser dado da carteira e acabar em um log.
    if _FORMATO_CNPJ.fullmatch(cnpj) is None:
        raise ValueError("CNPJ com formato inválido")
    if digitos_verificadores_cnpj(cnpj[:12]) != cnpj[12:]:
        raise ValueError("CNPJ com dígito verificador inválido")
    return cnpj
