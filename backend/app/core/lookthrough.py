"""Look-through: abre fundos em cadeia até chegar às empresas."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, localcontext
from enum import StrEnum

from app.core.composicao import (
    Categoria,
    Composicao,
    ItemComposicao,
    Posicao,
    TipoItem,
    categoria_do_item,
)

# Pesos com muitas casas multiplicados em cadeia passam dos 28 dígitos padrão.
PRECISAO = 50
# Num ciclo, para de dar voltas quando o valor que voltaria a um fundo fica abaixo
# desta fração do valor com que ele entrou no caminho. O resto vai para "não aberto".
CONVERGENCIA_CICLO = Decimal("0.001")
MAX_FUNDOS_DISTINTOS = 10  # fundos diferentes numa mesma cadeia
MAX_NIVEIS = 100  # trava para ciclos que não convergem (ex.: A 100% em B e B 100% em A)


class CodigoAviso(StrEnum):
    CICLO = "ciclo"
    CICLO_SEM_CONVERGENCIA = "ciclo_sem_convergencia"
    CADEIA_LONGA = "cadeia_longa"
    FUNDO_SEM_COMPOSICAO = "fundo_sem_composicao"


@dataclass(frozen=True, slots=True)
class Aviso:
    codigo: CodigoAviso
    fundo_isin: str


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
class ResumoFundo:
    """A composição do próprio fundo, como a fonte informa, e quanto da carteira passou
    por ele (somando todas as entradas, inclusive as voltas de um ciclo)."""

    isin: str
    data_referencia: date
    fonte: str
    aproximado_por: str | None
    pesos: dict[Categoria, Decimal]
    valor_recebido: Decimal = Decimal(0)


@dataclass
class ResultadoLookthrough:
    total: Decimal = Decimal(0)
    empresas: dict[str, ExposicaoEmpresa] = field(default_factory=dict)
    categorias: dict[Categoria, Decimal] = field(
        default_factory=lambda: {c: Decimal(0) for c in Categoria if c is not Categoria.FUNDOS}
    )
    derivativos_por_ativo_objeto: dict[str | None, Decimal] = field(default_factory=dict)
    avisos: set[Aviso] = field(default_factory=set)
    fundos: dict[str, ResumoFundo] = field(default_factory=dict)

    def _empresa(self, isin: str) -> ExposicaoEmpresa:
        if isin not in self.empresas:
            self.empresas[isin] = ExposicaoEmpresa(isin)
        return self.empresas[isin]

    def _nao_aberto(self, valor: Decimal, codigo: CodigoAviso, fundo_isin: str) -> None:
        self.categorias[Categoria.NAO_ABERTO] += valor
        self.avisos.add(Aviso(codigo, fundo_isin))


@dataclass(frozen=True, slots=True)
class _Pendente:
    item: ItemComposicao  # o peso do item já foi aplicado em valor
    valor: Decimal
    fundo_da_carteira: str | None  # None = posição direta
    # Fundos já abertos neste caminho, com o valor da primeira entrada de cada um.
    caminho: tuple[tuple[str, Decimal], ...] = ()
    nivel: int = 0


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
                pilha.extend(_abrir_fundo(r, atual, composicao))
            elif item.tipo is TipoItem.FUNDO and item.isin:
                r._nao_aberto(atual.valor, CodigoAviso.FUNDO_SEM_COMPOSICAO, item.isin)
            else:
                _registrar(r, atual)
    return r


def _abrir_fundo(
    r: ResultadoLookthrough, atual: _Pendente, composicao: Composicao
) -> list[_Pendente]:
    """Devolve os itens do fundo a abrir em seguida, ou nenhum se a cadeia parar aqui."""
    fundo = composicao.fundo_isin
    entradas = dict(atual.caminho)
    caminho = atual.caminho

    if atual.nivel >= MAX_NIVEIS:
        r._nao_aberto(atual.valor, CodigoAviso.CICLO_SEM_CONVERGENCIA, fundo)
        return []
    if fundo in entradas:
        r.avisos.add(Aviso(CodigoAviso.CICLO, fundo))
        if abs(atual.valor) < CONVERGENCIA_CICLO * abs(entradas[fundo]):
            r.categorias[Categoria.NAO_ABERTO] += atual.valor
            return []
    elif len(entradas) >= MAX_FUNDOS_DISTINTOS:
        r._nao_aberto(atual.valor, CodigoAviso.CADEIA_LONGA, fundo)
        return []
    else:
        caminho = (*caminho, (fundo, atual.valor))

    resumo = r.fundos.get(fundo)
    if resumo is None:
        resumo = r.fundos[fundo] = ResumoFundo(
            fundo,
            composicao.data_referencia,
            composicao.fonte,
            composicao.aproximado_por,
            composicao.pesos_por_categoria(),
        )
    resumo.valor_recebido += atual.valor

    sobra = resumo.pesos[Categoria.NAO_IDENTIFICADO]
    r.categorias[Categoria.NAO_IDENTIFICADO] += atual.valor * sobra
    origem = atual.fundo_da_carteira or fundo
    return [
        _Pendente(filho, atual.valor * filho.peso, origem, caminho, atual.nivel + 1)
        for filho in composicao.itens
        if filho.peso != 0
    ]


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
