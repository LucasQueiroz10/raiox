"""Esquemas de entrada e saída de POST /raiox.

Valores monetários trafegam como TEXTO ("1000.00"): na entrada, um número JSON passaria pelo
float antes de virar Decimal; na saída, o Pydantic já serializa Decimal como texto.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationInfo,
    WithJsonSchema,
    field_validator,
)
from pydantic_core import PydanticCustomError

from app.core.identificadores import (
    IsinForaDaLista,
    normalizar_cnpj,
    normalizar_isin_permitido,
    normalizar_ticker_b3,
    normalizar_ticker_eua,
)
from app.core.traducao import TipoIdentificador

MAX_POSICOES = 500
MAX_FUNDOS = 100


def _so_texto(valor: object) -> object:
    if not isinstance(valor, str):
        raise ValueError('valor deve ser enviado como texto, por exemplo "1000.00"')
    return valor


ValorEmTexto = Annotated[
    Decimal,
    BeforeValidator(_so_texto),
    Field(gt=0, max_digits=18, decimal_places=2),
    # Sem isto, o OpenAPI diria "número ou texto" e o tipo gerado no front aceitaria número.
    WithJsonSchema(
        {
            "type": "string",
            "description": "Valor maior que zero, em texto, com ponto e até 2 casas decimais",
            "examples": ["1000.00"],
        },
        mode="validation",
    ),
]


class _Estrito(BaseModel):
    model_config = ConfigDict(extra="forbid")


# Validação e normalização de cada tipo de identificador (ADR 0005, seção 5). As mensagens de erro
# nunca repetem o valor enviado.
_NORMALIZAR = {
    "isin": normalizar_isin_permitido,
    "ticker_b3": normalizar_ticker_b3,
    "ticker_eua": normalizar_ticker_eua,
    "cnpj": normalizar_cnpj,
}


class PosicaoEntrada(_Estrito):
    """Uma posição da carteira, pelo identificador (ADR 0005, seção 5).

    `tipo` é o que a pessoa declarou; para um ativo que a base conhece, vale o tipo da base. A ação
    americana entra só pelo ticker: o ISIN de país fora da lista permitida recebe 422 com o motivo
    "isin_fora_da_lista".
    """

    # Antes do identificador: o validador dele lê o tipo já validado.
    tipo_identificador: TipoIdentificador
    identificador: str
    valor: ValorEmTexto
    moeda: Literal["BRL", "USD"]
    tipo: Literal["acao", "fundo"]

    @field_validator("identificador")
    @classmethod
    def _identificador_valido(cls, identificador: str, info: ValidationInfo) -> str:
        tipo_identificador = info.data.get("tipo_identificador")
        if tipo_identificador is None:
            return identificador  # o tipo_identificador inválido já tem o seu erro
        try:
            return _NORMALIZAR[tipo_identificador](identificador)
        except IsinForaDaLista as erro:
            raise PydanticCustomError("isin_fora_da_lista", str(erro)) from None


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


class FatiaFii(BaseModel):
    """Os FIIs da carteira (diretos e dentro de fundos) de um tipo e, no tijolo, de um segmento
    (ADR 0008, etapa 4.3). segmento None: papel, fundo de fundos, genérico ou tijolo com vários
    segmentos."""

    tipo: Literal["tijolo", "papel", "fundo_de_fundos", "generico"]
    segmento: str | None
    valor: Decimal
    percentual: Decimal


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
    fiis_por_tipo: list[FatiaFii]  # maior primeiro
    derivativos_por_setor: list[Fatia]
    credito_por_setor: list[Fatia]
    vendido_por_setor: list[Fatia]
    empresas: list[Empresa]
    demais_empresas: DemaisEmpresas
    fundos: list[Fundo]
    avisos: list[Aviso]
