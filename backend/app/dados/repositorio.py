"""De onde a API tira os dados públicos: identificação, composições, ligação ativo -> empresa,
classificação e nomes.

Duas implementações: o PostgreSQL (app/dados/postgres.py), quando RX_BANCO_URL está definida, e o
conjunto de exemplo sintético (app/dados/exemplo.py), no desenvolvimento sem banco.
"""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from app.core.classificacao import TabelaClassificacao
from app.core.composicao import Composicao
from app.core.traducao import TabelaIdentificacao


@runtime_checkable
class RepositorioDados(Protocol):
    def identificacao(self) -> TabelaIdentificacao:
        """Como cada posição da carteira chega ao ativo_id: tickers, ISINs e o tipo de cada ativo
        da identificação vigente (ADR 0005, seção 5)."""
        ...

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


class FonteDados(Protocol):
    def foto(self) -> RepositorioDados:
        """Os dados de um momento só: uma análise inteira lê dados coerentes entre si."""
        ...

    def aquecer(self) -> bool:
        """Relê agora, se saiu carga nova (partida do servidor e aquecimento). Devolve se há
        dados prontos."""
        ...
