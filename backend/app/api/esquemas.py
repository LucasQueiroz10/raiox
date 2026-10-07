"""Esquemas de entrada e saída de POST /raiox.

Valores monetários trafegam como TEXTO ("1000.00"): na entrada, um número JSON passaria pelo
float antes de virar Decimal; na saída, o Pydantic já serializa Decimal como texto.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.core.identificadores import normalizar_isin

MAX_POSICOES = 500
MAX_FUNDOS = 100


def _so_texto(valor: object) -> object:
    if not isinstance(valor, str):
        raise ValueError('valor deve ser enviado como texto, por exemplo "1000.00"')
    return valor


ValorEmTexto = Annotated[
    Decimal, BeforeValidator(_so_texto), Field(gt=0, max_digits=18, decimal_places=2)
]


class _Estrito(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PosicaoEntrada(_Estrito):
    isin: str
    valor: ValorEmTexto
    moeda: Literal["BRL", "USD"]
    tipo: Literal["acao", "fundo"]

    @field_validator("isin")
    @classmethod
    def _isin_valido(cls, isin: str) -> str:
        return normalizar_isin(isin)


class EntradaRaioX(_Estrito):
    posicoes: list[PosicaoEntrada] = Field(min_length=1, max_length=MAX_POSICOES)

    @field_validator("posicoes")
    @classmethod
    def _limite_de_fundos(cls, posicoes: list[PosicaoEntrada]) -> list[PosicaoEntrada]:
        if sum(p.tipo == "fundo" for p in posicoes) > MAX_FUNDOS:
            raise ValueError(f"no máximo {MAX_FUNDOS} fundos por carteira")
        return posicoes


# ---- saída -------------------------------------------------------------------------------

CategoriaFatia = Literal["classificado", "nucleo", "sem_classificacao"]


class Fatia(BaseModel):
    """nome None = sem classificação (ou núcleo, em tema/subtema; ver categoria)."""

    nome: str | None
    categoria: CategoriaFatia
    valor: Decimal
    percentual: Decimal
    valor_preliminar: Decimal


class FatiaSubtema(Fatia):
    tema: str | None


class Cobertura(BaseModel):
    total_acoes: Decimal
    confirmada: Decimal
    preliminar: Decimal
    sem_classificacao: Decimal
    percentual_confirmada: Decimal
    percentual_preliminar: Decimal
    percentual_classificada: Decimal


class Tema(BaseModel):
    tema: str
    subtema: str
    peso: Decimal
    selo: str


class Classe(BaseModel):
    """Uma classe de ação da empresa (ex.: PN ou ON) e a parte dela na exposição comprada."""

    ativo_id: str | None  # None = chegou por fundo sem identificar a classe
    nome: str | None
    valor: Decimal
    percentual_da_empresa: Decimal


class Empresa(BaseModel):
    empresa_id: str
    nome: str | None
    setor: str | None
    selo_setor: str | None
    temas: list[Tema]
    direto: Decimal
    via_fundos: Decimal
    total: Decimal
    percentual: Decimal
    escondida: bool
    fundos: list[str]
    classes: list[Classe]  # maior primeiro


class DemaisEmpresas(BaseModel):
    quantidade: int
    valor: Decimal
    percentual: Decimal


class Fundo(BaseModel):
    fundo_id: str
    nome: str | None
    data_referencia: date
    fonte: str
    aproximado_por: str | None
    valor_recebido: Decimal
    pesos: dict[str, Decimal]


class Aviso(BaseModel):
    codigo: str
    fundo_id: str | None


class Ptax(BaseModel):
    valor: Decimal
    data_cotacao: date
    data_pedida: date


class RaioXResposta(BaseModel):
    total: Decimal
    versao_classificacao: str
    ptax: Ptax | None
    cobertura: Cobertura
    por_setor: list[Fatia]
    por_tema: list[Fatia]
    por_subtema: list[FatiaSubtema]
    categorias: dict[str, Decimal]
    derivativos_por_setor: list[Fatia]
    credito_por_setor: list[Fatia]
    vendido_por_setor: list[Fatia]
    empresas: list[Empresa]
    demais_empresas: DemaisEmpresas
    fundos: list[Fundo]
    avisos: list[Aviso]
