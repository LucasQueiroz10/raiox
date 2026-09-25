"""Agregação do raio-x: soma a exposição das empresas por setor, tema e subtema."""

from collections.abc import Hashable
from dataclasses import dataclass, field
from decimal import Decimal, localcontext

from app.core.classificacao import Selo, TabelaClassificacao
from app.core.lookthrough import PRECISAO, ResultadoLookthrough


@dataclass(frozen=True, slots=True)
class Fatia:
    valor: Decimal
    percentual: Decimal  # sobre o total da carteira
    valor_preliminar: Decimal  # parte do valor com classificação de selo "preliminar"


@dataclass(frozen=True, slots=True)
class RaioX:
    total: Decimal
    versao_classificacao: str
    # Chave None = sem classificação.
    por_setor: dict[str | None, Fatia] = field(default_factory=dict)


class _Somador:
    """Acumula valor e valor preliminar por chave e fecha em Fatias."""

    def __init__(self) -> None:
        self._valores: dict[Hashable, list[Decimal]] = {}

    def somar(self, chave: Hashable, valor: Decimal, preliminar: bool) -> None:
        soma = self._valores.setdefault(chave, [Decimal(0), Decimal(0)])
        soma[0] += valor
        if preliminar:
            soma[1] += valor

    def fatias(self, total: Decimal) -> dict:
        return {
            chave: Fatia(valor, valor / total if total else Decimal(0), preliminar)
            for chave, (valor, preliminar) in self._valores.items()
        }


def agregar(resultado: ResultadoLookthrough, tabela: TabelaClassificacao) -> RaioX:
    """Soma a exposição comprada em ações de cada empresa pelo setor dela."""
    with localcontext(prec=PRECISAO):
        por_setor = _Somador()
        for empresa in resultado.empresas.values():
            if empresa.total == 0:
                continue
            c = tabela.classificacoes.get(empresa.isin)
            if c is None:
                por_setor.somar(None, empresa.total, preliminar=False)
            else:
                por_setor.somar(c.setor, empresa.total, c.selo_setor is Selo.PRELIMINAR)

        return RaioX(
            total=resultado.total,
            versao_classificacao=tabela.versao,
            por_setor=por_setor.fatias(resultado.total),
        )
