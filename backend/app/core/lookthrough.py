"""Look-through: abre fundos em cadeia até chegar às empresas."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, localcontext

from app.core.composicao import Categoria, Composicao, Posicao, TipoItem, categoria_do_item

# Pesos com muitas casas multiplicados em cadeia passam dos 28 dígitos padrão.
PRECISAO = 50


@dataclass
class ExposicaoEmpresa:
    isin: str
    direto: Decimal = Decimal(0)  # ações que a pessoa tem na carteira
    via_fundos: Decimal = Decimal(0)  # ações que chegam por fundos
    fundos: set[str] = field(default_factory=set)  # fundos da carteira por onde chega

    @property
    def total(self) -> Decimal:
        return self.direto + self.via_fundos


@dataclass
class ResultadoLookthrough:
    total: Decimal = Decimal(0)
    empresas: dict[str, ExposicaoEmpresa] = field(default_factory=dict)
    categorias: dict[Categoria, Decimal] = field(
        default_factory=lambda: {c: Decimal(0) for c in Categoria if c is not Categoria.FUNDOS}
    )

    def _empresa(self, isin: str) -> ExposicaoEmpresa:
        if isin not in self.empresas:
            self.empresas[isin] = ExposicaoEmpresa(isin)
        return self.empresas[isin]


@dataclass(frozen=True, slots=True)
class _Pendente:
    isin: str | None
    valor: Decimal
    tipo: TipoItem
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
            pilha.append(_Pendente(p.isin, p.valor_brl, p.tipo, None))

        while pilha:
            atual = pilha.pop()
            composicao = composicoes.get(atual.isin) if atual.isin else None
            if composicao is not None:
                origem = atual.fundo_da_carteira or atual.isin
                for item in composicao.itens:
                    valor = atual.valor * item.peso
                    pilha.append(_Pendente(item.isin, valor, item.tipo, origem))
                continue

            categoria = categoria_do_item(atual.tipo, atual.valor)
            r.categorias[categoria] += atual.valor
            if atual.tipo is TipoItem.ACAO and atual.isin:
                empresa = r._empresa(atual.isin)
                if atual.fundo_da_carteira is None:
                    empresa.direto += atual.valor
                else:
                    empresa.via_fundos += atual.valor
                    empresa.fundos.add(atual.fundo_da_carteira)
    return r
