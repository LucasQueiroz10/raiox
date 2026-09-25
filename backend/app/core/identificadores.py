"""Identificadores de títulos. O ISIN é a chave interna de empresa."""


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
