"""Identificadores de títulos. O ISIN é a chave interna de empresa."""

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
