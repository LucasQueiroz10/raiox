"""De onde a API tira os dados públicos: composições, classificação e nomes.

Hoje a implementação é um conjunto de exemplo sintético (app/dados/exemplo.py).
Quando o banco existir, entra outra implementação com a mesma interface.
"""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from app.core.classificacao import TabelaClassificacao
from app.core.composicao import Composicao


@runtime_checkable
class RepositorioDados(Protocol):
    def composicoes(self) -> Mapping[str, Composicao]:
        """Composição mais recente de cada fundo, por ISIN do fundo."""
        ...

    def tabela_classificacao(self) -> TabelaClassificacao:
        """Classificação vigente de cada empresa, com a versão da tabela."""
        ...

    def nome(self, isin: str) -> str | None:
        """Nome da empresa ou do fundo, ou None se desconhecido."""
        ...
