"""Agregação do raio-x: soma a exposição das empresas por setor, tema e subtema."""

from collections.abc import Hashable
from dataclasses import dataclass, field
from decimal import Decimal, localcontext

from app.core.classificacao import ParticipacaoTema, Selo, TabelaClassificacao
from app.core.lookthrough import PRECISAO, ResultadoLookthrough


@dataclass(frozen=True, slots=True)
class EmpresaRaioX:
    isin: str
    setor: str | None  # None = sem classificação
    selo_setor: Selo | None
    temas: tuple[ParticipacaoTema, ...]
    direto: Decimal
    via_fundos: Decimal
    total: Decimal
    percentual: Decimal  # sobre o total da carteira
    escondida: bool  # chega por pelo menos um fundo
    fundos: frozenset[str]  # fundos da carteira por onde chega


@dataclass(frozen=True, slots=True)
class Fatia:
    valor: Decimal
    percentual: Decimal  # sobre o total da carteira
    valor_preliminar: Decimal  # parte do valor com classificação de selo "preliminar"


@dataclass(frozen=True, slots=True)
class Cobertura:
    """Quanto do valor em ações tem setor classificado. Caixa, títulos públicos,
    derivativos e não identificado não têm setor e ficam fora da base."""

    total_acoes: Decimal
    confirmada: Decimal
    preliminar: Decimal
    sem_classificacao: Decimal
    percentual_confirmada: Decimal
    percentual_preliminar: Decimal
    percentual_classificada: Decimal

    @classmethod
    def calcular(cls, por_setor: dict[str | None, Fatia]) -> Cobertura:
        classificadas = [f for s, f in por_setor.items() if s is not None]
        preliminar = sum((f.valor_preliminar for f in classificadas), Decimal(0))
        confirmada = sum((f.valor for f in classificadas), Decimal(0)) - preliminar
        sem = por_setor[None].valor if None in por_setor else Decimal(0)
        total = confirmada + preliminar + sem

        def fracao(v: Decimal) -> Decimal:
            return v / total if total else Decimal(0)

        return cls(
            total,
            confirmada,
            preliminar,
            sem,
            fracao(confirmada),
            fracao(preliminar),
            fracao(confirmada + preliminar),
        )


@dataclass(frozen=True, slots=True)
class RaioX:
    total: Decimal
    versao_classificacao: str
    cobertura: Cobertura
    # Chave None = sem classificação (setor) ou sem tema (núcleo + sem classificação).
    por_setor: dict[str | None, Fatia] = field(default_factory=dict)
    por_tema: dict[str | None, Fatia] = field(default_factory=dict)
    por_subtema: dict[tuple[str, str] | None, Fatia] = field(default_factory=dict)
    # Fora da exposição em ações: mostrados à parte, pelo setor da empresa ligada.
    derivativos_por_setor: dict[str | None, Fatia] = field(default_factory=dict)
    credito_por_setor: dict[str | None, Fatia] = field(default_factory=dict)
    vendido_por_setor: dict[str | None, Fatia] = field(default_factory=dict)
    # Empresas com exposição em ações, maiores primeiro.
    empresas: tuple[EmpresaRaioX, ...] = ()


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
    """Soma a exposição comprada em ações de cada empresa pelo setor dela e divide o
    valor pelos temas conforme o peso de cada um; o núcleo fica sem tema."""
    with localcontext(prec=PRECISAO):
        por_setor, por_tema, por_subtema = _Somador(), _Somador(), _Somador()
        for empresa in resultado.empresas.values():
            valor = empresa.total
            if valor == 0:
                continue
            c = tabela.classificacoes.get(empresa.isin)
            if c is None:
                por_setor.somar(None, valor, preliminar=False)
                por_tema.somar(None, valor, preliminar=False)
                por_subtema.somar(None, valor, preliminar=False)
                continue

            por_setor.somar(c.setor, valor, c.selo_setor is Selo.PRELIMINAR)
            for t in c.temas:
                preliminar = t.selo is Selo.PRELIMINAR
                por_tema.somar(t.tema, valor * t.peso, preliminar)
                por_subtema.somar((t.tema, t.subtema), valor * t.peso, preliminar)
            por_tema.somar(None, valor * c.peso_nucleo, preliminar=False)
            por_subtema.somar(None, valor * c.peso_nucleo, preliminar=False)

        derivativos, credito, vendido = _Somador(), _Somador(), _Somador()
        for objeto, valor in resultado.derivativos_por_ativo_objeto.items():
            _somar_pelo_setor(derivativos, tabela, objeto, valor)
        for empresa in resultado.empresas.values():
            if empresa.credito:
                _somar_pelo_setor(credito, tabela, empresa.isin, empresa.credito)
            if empresa.vendido:
                _somar_pelo_setor(vendido, tabela, empresa.isin, empresa.vendido)

        total = resultado.total
        setores = por_setor.fatias(total)
        return RaioX(
            total=total,
            versao_classificacao=tabela.versao,
            cobertura=Cobertura.calcular(setores),
            por_setor=setores,
            por_tema=por_tema.fatias(total),
            por_subtema=por_subtema.fatias(total),
            derivativos_por_setor=derivativos.fatias(total),
            credito_por_setor=credito.fatias(total),
            vendido_por_setor=vendido.fatias(total),
            empresas=_listar_empresas(resultado, tabela),
        )


def _listar_empresas(
    resultado: ResultadoLookthrough, tabela: TabelaClassificacao
) -> tuple[EmpresaRaioX, ...]:
    total = resultado.total
    lista = []
    for e in resultado.empresas.values():
        if e.total == 0:
            continue
        c = tabela.classificacoes.get(e.isin)
        lista.append(
            EmpresaRaioX(
                isin=e.isin,
                setor=c.setor if c else None,
                selo_setor=c.selo_setor if c else None,
                temas=c.temas if c else (),
                direto=e.direto,
                via_fundos=e.via_fundos,
                total=e.total,
                percentual=e.total / total if total else Decimal(0),
                escondida=e.via_fundos != 0,
                fundos=frozenset(e.fundos),
            )
        )
    return tuple(sorted(lista, key=lambda e: (-e.total, e.isin)))


def _somar_pelo_setor(
    somador: _Somador, tabela: TabelaClassificacao, isin: str | None, valor: Decimal
) -> None:
    c = tabela.classificacoes.get(isin) if isin else None
    if c is None:
        somador.somar(None, valor, preliminar=False)
    else:
        somador.somar(c.setor, valor, c.selo_setor is Selo.PRELIMINAR)
