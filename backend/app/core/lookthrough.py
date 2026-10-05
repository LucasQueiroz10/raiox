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
# Trava total contra composições com erro (pesos somando mais de 100% dentro de ciclos
# multiplicam os caminhos). Carteiras reais, mesmo com ETFs de milhares de ações, ficam
# bem abaixo.
MAX_PASSOS = 1_000_000


class CodigoAviso(StrEnum):
    CICLO = "ciclo"
    CICLO_SEM_CONVERGENCIA = "ciclo_sem_convergencia"
    CADEIA_LONGA = "cadeia_longa"
    FUNDO_SEM_COMPOSICAO = "fundo_sem_composicao"
    LIMITE_DE_PROCESSAMENTO = "limite_de_processamento"


@dataclass(frozen=True, slots=True)
class Aviso:
    codigo: CodigoAviso
    fundo_id: str | None  # None quando o aviso vale para a carteira toda


@dataclass
class ExposicaoEmpresa:
    empresa_id: str
    direto: Decimal = Decimal(0)  # ações que a pessoa tem na carteira
    via_fundos: Decimal = Decimal(0)  # ações que chegam por fundos
    vendido: Decimal = Decimal(0)  # vendas a descoberto dentro de fundos (negativo)
    credito: Decimal = Decimal(0)  # debêntures e outros títulos emitidos pela empresa
    fundos: set[str] = field(default_factory=set)  # fundos da carteira por onde chega
    # Parte comprada de cada classe (ativo_id); None = item de fundo sem ativo_id.
    por_ativo: dict[str | None, Decimal] = field(default_factory=dict)

    @property
    def total(self) -> Decimal:
        """Exposição comprada em ações; vendido e crédito ficam à parte."""
        return self.direto + self.via_fundos


@dataclass
class ResumoFundo:
    """A composição do próprio fundo, como a fonte informa, e quanto da carteira passou
    por ele (somando todas as entradas, inclusive as voltas de um ciclo)."""

    fundo_id: str
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
    # Pela empresa do ativo-objeto; None = derivativo sem ativo-objeto.
    derivativos_por_empresa: dict[str | None, Decimal] = field(default_factory=dict)
    avisos: set[Aviso] = field(default_factory=set)
    fundos: dict[str, ResumoFundo] = field(default_factory=dict)

    def _empresa(self, empresa_id: str) -> ExposicaoEmpresa:
        if empresa_id not in self.empresas:
            self.empresas[empresa_id] = ExposicaoEmpresa(empresa_id)
        return self.empresas[empresa_id]

    def _nao_aberto(self, valor: Decimal, codigo: CodigoAviso, fundo_id: str | None) -> None:
        self.categorias[Categoria.NAO_ABERTO] += valor
        self.avisos.add(Aviso(codigo, fundo_id))


@dataclass(frozen=True, slots=True)
class _Pendente:
    item: ItemComposicao  # o peso do item já foi aplicado em valor
    valor: Decimal
    fundo_da_carteira: str | None  # None = posição direta
    # Fundos já abertos neste caminho, com o valor da primeira entrada de cada um.
    caminho: tuple[tuple[str, Decimal], ...] = ()
    nivel: int = 0


def abrir_carteira(
    posicoes: Iterable[Posicao],
    composicoes: Mapping[str, Composicao],
    *,
    empresa_do_ativo: Mapping[str, str] | None = None,
    max_passos: int = MAX_PASSOS,
) -> ResultadoLookthrough:
    """Distribui o valor de cada posição até as empresas, sem normalizar pesos.

    empresa_do_ativo liga cada ação (ativo_id) à empresa emissora (empresa_id), para as classes da
    mesma empresa somarem juntas (ADR 0005). Ação fora dela é a própria empresa.

    Usado pela API e, pela X-03, também pelo lote do IrRAE (DT-9: Decimal é mais lento que float).
    """
    r = ResultadoLookthrough()
    ligacao = empresa_do_ativo or {}
    with localcontext(prec=PRECISAO):
        pilha = []
        for p in posicoes:
            r.total += p.valor_brl
            item = ItemComposicao(p.ativo_id, Decimal(1), p.tipo)
            pilha.append(_Pendente(item, p.valor_brl, None))

        passos = 0
        while pilha:
            passos += 1
            if passos > max_passos:
                restante = sum(p.valor for p in pilha)
                r._nao_aberto(restante, CodigoAviso.LIMITE_DE_PROCESSAMENTO, None)
                break
            atual = pilha.pop()
            item = atual.item
            composicao = composicoes.get(item.ativo_id) if item.ativo_id else None
            if composicao is not None:
                pilha.extend(_abrir_fundo(r, atual, composicao))
            elif item.tipo is TipoItem.FUNDO and item.ativo_id:
                r._nao_aberto(atual.valor, CodigoAviso.FUNDO_SEM_COMPOSICAO, item.ativo_id)
            else:
                _registrar(r, atual, ligacao)
    return r


def _abrir_fundo(
    r: ResultadoLookthrough, atual: _Pendente, composicao: Composicao
) -> list[_Pendente]:
    """Devolve os itens do fundo a abrir em seguida, ou nenhum se a cadeia parar aqui."""
    fundo = composicao.fundo_id
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


def _registrar(
    r: ResultadoLookthrough, atual: _Pendente, empresa_do_ativo: Mapping[str, str]
) -> None:
    item, valor, origem = atual.item, atual.valor, atual.fundo_da_carteira
    categoria = categoria_do_item(item.tipo, valor)
    r.categorias[categoria] += valor

    if categoria is Categoria.DERIVATIVOS:
        objeto = item.ativo_objeto
        chave = empresa_do_ativo.get(objeto, objeto) if objeto else None
        r.derivativos_por_empresa[chave] = r.derivativos_por_empresa.get(chave, Decimal(0)) + valor
        return

    if categoria is Categoria.CREDITO and item.emissor:
        empresa = r._empresa(item.emissor)
        empresa.credito += valor
    elif categoria in (Categoria.ACOES, Categoria.VENDIDO) and (item.ativo_id or item.empresa_id):
        if item.empresa_id:
            empresa = r._empresa(item.empresa_id)
        else:
            empresa = r._empresa(empresa_do_ativo.get(item.ativo_id, item.ativo_id))
        if categoria is Categoria.VENDIDO:
            empresa.vendido += valor
        else:
            empresa.por_ativo[item.ativo_id] = (
                empresa.por_ativo.get(item.ativo_id, Decimal(0)) + valor
            )
            if origem is None:
                empresa.direto += valor
            else:
                empresa.via_fundos += valor
    else:
        return
    if origem is not None:
        empresa.fundos.add(origem)
