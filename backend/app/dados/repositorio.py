"""De onde a API tira os dados públicos: composições, ligação ativo -> empresa, classificação e
nomes.

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
        """Composição mais recente de cada fundo, pelo fundo_id."""
        ...

    def empresa_do_ativo(self) -> Mapping[str, str]:
        """Empresa emissora (empresa_id) de cada ação (ativo_id); ADR 0005."""
        ...

    def tabela_classificacao(self) -> TabelaClassificacao:
        """Classificação vigente de cada empresa (pelo empresa_id), com a versão da tabela."""
        ...

    def nome(self, identificador: str) -> str | None:
        """Nome da empresa, da classe de ação ou do fundo, ou None se desconhecido."""
        ...
