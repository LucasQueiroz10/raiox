"""Validações comuns antes de publicar uma carga (ADR 0006, seção 5).

Varredura de CPF: o CPF nunca é gravado (LGPD; ADR 0008, seção 3). Os leitores já descartam o
emissor pessoa física, e esta varredura é a segunda barreira, pedida pelo M1: antes de publicar,
procura nas linhas preparadas qualquer número com formato e dígitos verificadores de CPF. Se achar,
a carga não publica, e o motivo diz a coluna e o id público da linha (o CNPJ do fundo, o empresa_id
ou o ativo_id), para achar a linha na fonte; nunca o número.
"""

import re
from collections.abc import Iterable, Sequence

from cargas.rotina import ErroDeValidacao

# 11 dígitos seguidos ou com a máscara 999.999.999-99, soltos: sem letra ou número colado antes ou
# depois. Assim o número não é confundido com um pedaço de CNPJ (14 dígitos) ou de um identificador
# com letras (ex.: CNPJ alfanumérico).
_CPF = re.compile(
    r"(?<![0-9A-Za-z])(?:[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})(?![0-9A-Za-z])"
)


def cpf_valido(numero: str) -> bool:
    """Diz se os 11 dígitos têm os dígitos verificadores de um CPF (módulo 11 da Receita Federal).
    Dígitos todos iguais (ex.: 111.111.111-11) não são CPF válido."""
    if len(numero) != 11 or not numero.isdigit() or len(set(numero)) == 1:
        return False
    digitos = [int(c) for c in numero]
    for posicao in (9, 10):
        soma = sum(
            d * peso for d, peso in zip(digitos[:posicao], range(posicao + 1, 1, -1), strict=True)
        )
        if (soma * 10) % 11 % 10 != digitos[posicao]:
            return False
    return True


def _tem_cpf(valor: object) -> bool:
    return isinstance(valor, str) and any(
        cpf_valido(re.sub(r"[^0-9]", "", achado)) for achado in _CPF.findall(valor)
    )


def conferir_sem_cpf(
    linhas: Iterable[Sequence[object]], colunas: Sequence[str], *, chave: str | None = None
) -> None:
    """Levanta ErroDeValidacao se algum texto das linhas tiver um CPF válido. A mensagem diz a
    coluna e, com `chave` (a coluna do id público da linha, ex.: "fundo_id"), o id; nunca o número.
    O id fica de fora se o CPF estiver nele."""
    posicao_da_chave = colunas.index(chave) if chave else None
    for linha in linhas:
        for coluna, valor in zip(colunas, linha, strict=True):
            if not _tem_cpf(valor):
                continue
            mensagem = f"número com formato de CPF na coluna {coluna}"
            if posicao_da_chave is not None and not _tem_cpf(linha[posicao_da_chave]):
                mensagem += f" ({chave} {linha[posicao_da_chave]})"
            raise ErroDeValidacao(mensagem)
