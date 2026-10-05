"""Agregação do raio-x: soma a exposição das empresas por setor, tema e subtema."""

from collections.abc import Hashable
from dataclasses import dataclass, field
from decimal import Decimal, localcontext

from app.core.classificacao import ParticipacaoTema, Selo, TabelaClassificacao
from app.core.lookthrough import PRECISAO, ResultadoLookthrough

# Chave de tema/subtema para a parte da empresa que sabemos que NÃO é de tema nenhum
# (a atividade do setor oficial). Diferente de None, que é "sem classificação":
# não sabemos se é de algum tema (ausente ≠ zero).
NUCLEO = "nucleo"


@dataclass(frozen=True, slots=True)
class EmpresaRaioX:
    empresa_id: str
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
    # Chave None = sem classificação. Em tema e subtema, NUCLEO = classificada e fora de tema.
    por_setor: dict[str | None, Fatia] = field(default_factory=dict)
    por_tema: dict[str | None, Fatia] = field(default_factory=dict)
    por_subtema: dict[tuple[str, str] | str | None, Fatia] = field(default_factory=dict)
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
            c = tabela.classificacoes.get(empresa.empresa_id)
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
            por_tema.somar(NUCLEO, valor * c.peso_nucleo, preliminar=False)
            por_subtema.somar(NUCLEO, valor * c.peso_nucleo, preliminar=False)

        derivativos, credito, vendido = _Somador(), _Somador(), _Somador()
        for objeto, valor in resultado.derivativos_por_ativo_objeto.items():
            _somar_pelo_setor(derivativos, tabela, objeto, valor)
        for empresa in resultado.empresas.values():
            if empresa.credito:
                _somar_pelo_setor(credito, tabela, empresa.empresa_id, empresa.credito)
            if empresa.vendido:
                _somar_pelo_setor(vendido, tabela, empresa.empresa_id, empresa.vendido)

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
        c = tabela.classificacoes.get(e.empresa_id)
        lista.append(
            EmpresaRaioX(
                empresa_id=e.empresa_id,
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
    return tuple(sorted(lista, key=lambda e: (-e.total, e.empresa_id)))


def _somar_pelo_setor(
    somador: _Somador, tabela: TabelaClassificacao, empresa_id: str | None, valor: Decimal
) -> None:
    c = tabela.classificacoes.get(empresa_id) if empresa_id else None
    if c is None:
        somador.somar(None, valor, preliminar=False)
    else:
        somador.somar(c.setor, valor, c.selo_setor is Selo.PRELIMINAR)
