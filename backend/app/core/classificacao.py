"""Classificação de empresas: setor oficial e participação em temas e subtemas."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum


class Origem(StrEnum):
    MANUAL = "manual"  # revisão humana, empresa por empresa
    OFICIAL = "oficial"  # SIC da SEC, setor da CVM, via tabela revisada à mão
    WIKIDATA = "wikidata"
    IA = "ia"
    MODELO_IRRAE = "modelo_irrae"


class Status(StrEnum):
    RASCUNHO = "rascunho"
    APROVADO = "aprovado"


class Selo(StrEnum):
    """O que a tela mostra ao lado de cada classificação."""

    CONFIRMADA = "confirmada"
    PRELIMINAR = "preliminar"


# Origens que já passaram por revisão humana entram aprovadas; as demais (inclusive
# tudo que vem de IA) entram como rascunho, conforme o CLAUDE.md.
_ORIGENS_REVISADAS = {Origem.MANUAL, Origem.OFICIAL}


def _status_inicial(origem: Origem) -> Status:
    return Status.APROVADO if origem in _ORIGENS_REVISADAS else Status.RASCUNHO


def _selo(status: Status) -> Selo:
    return Selo.CONFIRMADA if status is Status.APROVADO else Selo.PRELIMINAR


@dataclass(frozen=True, slots=True)
class ParticipacaoTema:
    """Fração do patrimônio da empresa ligada a um subtema (ex.: Cadeia de IA › Nuvem)."""

    tema: str
    subtema: str
    peso: Decimal
    origem: Origem = Origem.MODELO_IRRAE
    status: Status | None = None  # None: definido pela origem

    def __post_init__(self) -> None:
        if self.peso <= 0:
            raise ValueError("peso de tema precisa ser positivo")
        if self.status is None:
            object.__setattr__(self, "status", _status_inicial(self.origem))

    @property
    def selo(self) -> Selo:
        return _selo(self.status)


@dataclass(frozen=True, slots=True)
class Classificacao:
    isin: str
    setor: str
    temas: tuple[ParticipacaoTema, ...] = ()
    setor_origem: Origem = Origem.OFICIAL
    setor_status: Status | None = None  # None: definido pela origem

    def __post_init__(self) -> None:
        if sum(t.peso for t in self.temas) > 1:
            raise ValueError("a soma dos pesos dos temas passa de 100%")
        if self.setor_status is None:
            object.__setattr__(self, "setor_status", _status_inicial(self.setor_origem))

    @property
    def peso_nucleo(self) -> Decimal:
        """Fração que fica na atividade do setor oficial, sem tema."""
        return 1 - sum((t.peso for t in self.temas), Decimal(0))

    @property
    def selo_setor(self) -> Selo:
        return _selo(self.setor_status)


@dataclass(frozen=True, slots=True)
class TabelaClassificacao:
    versao: str
    classificacoes: Mapping[str, Classificacao] = field(default_factory=dict)
