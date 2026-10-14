"""O que é comum aos arquivos do portal de dados abertos da CVM (CDA, FCA e informes de FII).

Todos vêm em CSV dentro de zip, em latin-1, com separador `;` e números com ponto decimal. Os
leitores conferem as colunas de cada arquivo: uma coluna a mais ou a menos é mudança de formato, e a
leitura para (LayoutInesperado), para a carga não publicar e avisar (pedido do M1; ADR 0008).
"""

import csv
import io
import re
import zipfile
from collections.abc import Iterator, Sequence
from decimal import Decimal

from app.core.identificadores import normalizar_cnpj

# Só o formato "-123.45": recusa vírgula decimal, notação científica, "NaN" e "Infinity" (que o
# Decimal aceitaria).
_VALOR = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")


class LayoutInesperado(ValueError):
    """Os arquivos não estão no formato que o leitor conhece. A carga não publica."""


def linhas_csv(z: zipfile.ZipFile, nome: str, colunas: Sequence[str]) -> Iterator[dict[str, str]]:
    """As linhas do arquivo `nome` do zip, como dicionários. Levanta LayoutInesperado se as
    colunas não forem exatamente `colunas` (a ordem não importa)."""
    if nome not in z.namelist():
        raise LayoutInesperado(f"falta o arquivo {nome}")
    with z.open(nome) as bruto:
        texto = io.TextIOWrapper(bruto, encoding="latin-1", newline="")
        leitor = csv.DictReader(texto, delimiter=";")
        achadas, esperadas = set(leitor.fieldnames or ()), set(colunas)
        if achadas != esperadas:
            raise LayoutInesperado(
                f"{nome}: colunas fora do esperado: faltam {sorted(esperadas - achadas)}; "
                f"sobram {sorted(achadas - esperadas)}"
            )
        yield from leitor


def valor(texto: str) -> Decimal | None:
    """O número do texto, ou None se estiver fora do formato."""
    texto = texto.strip()
    return Decimal(texto) if _VALOR.fullmatch(texto) else None


def cnpj(texto: str) -> str | None:
    """O CNPJ sem máscara (14 caracteres), ou None se for inválido."""
    try:
        return normalizar_cnpj(texto)
    except ValueError:
        return None
