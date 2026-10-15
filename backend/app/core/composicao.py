"""Composição de fundos e ETFs por data, e as posições da carteira."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class TipoItem(StrEnum):
    ACAO = "acao"
    FUNDO = "fundo"
    CAIXA = "caixa"
    DERIVATIVO = "derivativo"
    CREDITO = "credito"  # debêntures e outros títulos de empresas
    TITULO_PUBLICO = "titulo_publico"
    OUTRO = "outro"


class Categoria(StrEnum):
    """Como cada parte do dinheiro aparece no raio-x."""

    ACOES = "acoes"
    VENDIDO = "vendido"  # ações com peso negativo (venda a descoberto)
    FUNDOS = "fundos"
    CAIXA = "caixa"
    DERIVATIVOS = "derivativos"  # valor de mercado, não a exposição econômica
    CREDITO = "credito"
    TITULOS_PUBLICOS = "titulos_publicos"
    OUTROS = "outros"
    NAO_IDENTIFICADO = "nao_identificado"  # o que falta ou sobra para 100%
    NAO_ABERTO = "nao_aberto"  # ciclo, cadeia longa demais ou fundo sem composição


class TipoFII(StrEnum):
    """Tipo de fundo imobiliário pela carteira do informe mensal da CVM: o grupo com mais da metade
    do investido (regra em ingest/cvm_fii.py; matriz de dados, fonte 36)."""

    TIJOLO = "tijolo"
    PAPEL = "papel"
    FUNDO_DE_FUNDOS = "fundo_de_fundos"
    GENERICO = "generico"  # sem grupo com mais da metade, ou sem carteira informada


_CATEGORIA_DO_TIPO = {
    TipoItem.ACAO: Categoria.ACOES,
    TipoItem.FUNDO: Categoria.FUNDOS,
    TipoItem.CAIXA: Categoria.CAIXA,
    TipoItem.DERIVATIVO: Categoria.DERIVATIVOS,
    TipoItem.CREDITO: Categoria.CREDITO,
    TipoItem.TITULO_PUBLICO: Categoria.TITULOS_PUBLICOS,
    TipoItem.OUTRO: Categoria.OUTROS,
}


def categoria_do_item(tipo: TipoItem, peso: Decimal) -> Categoria:
    if tipo is TipoItem.ACAO and peso < 0:
        return Categoria.VENDIDO
    return _CATEGORIA_DO_TIPO[tipo]


@dataclass(frozen=True, slots=True)
class Posicao:
    """Uma linha da carteira, já convertida para reais."""

    ativo_id: str
    valor_brl: Decimal
    tipo: TipoItem


@dataclass(frozen=True, slots=True)
class ItemComposicao:
    ativo_id: str | None  # caixa e alguns derivativos não têm identificador
    peso: Decimal  # fração do patrimônio do fundo; pode ser negativa
    tipo: TipoItem
    ativo_objeto: str | None = None  # só para derivativos: ativo_id do ativo-objeto
    emissor: str | None = None  # só para crédito: empresa_id da empresa emissora
    # Só para ação sem ativo_id (ex.: N-PORT, que não traz ticker): a empresa, direto.
    empresa_id: str | None = None


@dataclass(frozen=True, slots=True)
class Composicao:
    fundo_id: str  # ativo_id do fundo
    data_referencia: date
    fonte: str
    itens: tuple[ItemComposicao, ...]
    aproximado_por: str | None = None  # UCITS aproximado pelo ETF americano deste ativo_id

    def pesos_por_categoria(self) -> dict[Categoria, Decimal]:
        """Peso de cada categoria no fundo, sem normalizar; a diferença para 100% fica
        em NAO_IDENTIFICADO."""
        pesos = {c: Decimal(0) for c in Categoria if c is not Categoria.NAO_ABERTO}
        for item in self.itens:
            pesos[categoria_do_item(item.tipo, item.peso)] += item.peso
        pesos[Categoria.NAO_IDENTIFICADO] = 1 - sum(item.peso for item in self.itens)
        return pesos
