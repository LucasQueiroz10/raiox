"""Look-through: abre fundos em cadeia até chegar às empresas."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, localcontext

from app.core.composicao import (
    Categoria,
    Composicao,
    ItemComposicao,
    Posicao,
    categoria_do_item,
)

# Pesos com muitas casas multiplicados em cadeia passam dos 28 dígitos padrão.
PRECISAO = 50


@dataclass
class ExposicaoEmpresa:
    isin: str
    direto: Decimal = Decimal(0)  # ações que a pessoa tem na carteira
    via_fundos: Decimal = Decimal(0)  # ações que chegam por fundos
    vendido: Decimal = Decimal(0)  # vendas a descoberto dentro de fundos (negativo)
    credito: Decimal = Decimal(0)  # debêntures e outros títulos emitidos pela empresa
    fundos: set[str] = field(default_factory=set)  # fundos da carteira por onde chega

    @property
    def total(self) -> Decimal:
        """Exposição comprada em ações; vendido e crédito ficam à parte."""
        return self.direto + self.via_fundos


@dataclass
class ResultadoLookthrough:
    total: Decimal = Decimal(0)
    empresas: dict[str, ExposicaoEmpresa] = field(default_factory=dict)
    categorias: dict[Categoria, Decimal] = field(
        default_factory=lambda: {c: Decimal(0) for c in Categoria if c is not Categoria.FUNDOS}
    )
    derivativos_por_ativo_objeto: dict[str | None, Decimal] = field(default_factory=dict)

    def _empresa(self, isin: str) -> ExposicaoEmpresa:
        if isin not in self.empresas:
            self.empresas[isin] = ExposicaoEmpresa(isin)
        return self.empresas[isin]


@dataclass(frozen=True, slots=True)
class _Pendente:
    item: ItemComposicao  # o peso do item já foi aplicado em valor
    valor: Decimal
    fundo_da_carteira: str | None  # None = posição direta


def abrir_carteira(
    posicoes: Iterable[Posicao], composicoes: Mapping[str, Composicao]
) -> ResultadoLookthrough:
    """Distribui o valor de cada posição até as empresas, sem normalizar pesos."""
    r = ResultadoLookthrough()
    with localcontext(prec=PRECISAO):
        pilha = []
        for p in posicoes:
            r.total += p.valor_brl
            item = ItemComposicao(p.isin, Decimal(1), p.tipo)
            pilha.append(_Pendente(item, p.valor_brl, None))

        while pilha:
            atual = pilha.pop()
            item = atual.item
            composicao = composicoes.get(item.isin) if item.isin else None
            if composicao is not None:
                origem = atual.fundo_da_carteira or item.isin
                for filho in composicao.itens:
                    pilha.append(_Pendente(filho, atual.valor * filho.peso, origem))
                sobra = 1 - sum(filho.peso for filho in composicao.itens)
                r.categorias[Categoria.NAO_IDENTIFICADO] += atual.valor * sobra
                continue
            _registrar(r, atual)
    return r


def _registrar(r: ResultadoLookthrough, atual: _Pendente) -> None:
    item, valor, origem = atual.item, atual.valor, atual.fundo_da_carteira
    categoria = categoria_do_item(item.tipo, valor)
    r.categorias[categoria] += valor

    if categoria is Categoria.DERIVATIVOS:
        objeto = item.ativo_objeto_isin
        r.derivativos_por_ativo_objeto[objeto] = (
            r.derivativos_por_ativo_objeto.get(objeto, Decimal(0)) + valor
        )
        return

    if categoria is Categoria.CREDITO and item.emissor_isin:
        empresa = r._empresa(item.emissor_isin)
        empresa.credito += valor
    elif categoria in (Categoria.ACOES, Categoria.VENDIDO) and item.isin:
        empresa = r._empresa(item.isin)
        if categoria is Categoria.VENDIDO:
            empresa.vendido += valor
        elif origem is None:
            empresa.direto += valor
        else:
            empresa.via_fundos += valor
    else:
        return
    if origem is not None:
        empresa.fundos.add(origem)
