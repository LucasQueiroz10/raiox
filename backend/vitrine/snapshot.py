"""Contrato do snapshot da vitrine: o arquivo JSON que o lote grava e o site lê (ADR 0009).

Formato da seção 4 de docs/vitrine/especificacao.md. O site é estático e não valida o arquivo por
inteiro no navegador (a CSP sem eval impede os validadores de JSON Schema; ADR 0009, seção 2):
quem garante o contrato é este modelo, no lote e no CI. Por isso as regras ficam todas aqui:

- pesos e faixas em Decimal (backend/CLAUDE.md), gravados no JSON como número;
- tudo o que precisa fechar 100% fecha, e a exposição bate com as empresas;
- a faixa da carteira é a soma comonotônica dos quantis (cenário da especificação; a escolha entre
  um e dois cenários é a V-09 do ADR 0009, com o M1);
- taxonomia, componentes e limiares do selo vêm de irrae/config, nunca digitados aqui;
- campos extras são recusados: não há onde guardar CUSIP ou ISIN americano (ADR 0005);
- link de fonte só https e só nos domínios das fontes permitidas (S-1 do ADR 0009).
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    PositiveInt,
    model_validator,
)

from app.core.identificadores import cnpj_valido

_CONFIG_IRRAE = Path(__file__).resolve().parents[1] / "irrae" / "config"


def _ler_config(nome: str) -> dict:
    return json.loads((_CONFIG_IRRAE / nome).read_text(encoding="utf-8"))


_TAXONOMIA = _ler_config("taxonomia.json")["temas"]
_COMPONENTES_CFG = _ler_config("componentes.json")
# Nome de cada componente do IrRAE, na ordem da configuração.
COMPONENTES: dict[str, str] = {
    chave: valor["nome"] for chave, valor in _COMPONENTES_CFG["componentes"].items()
}
COMPONENTE_PRIOR = "prior_setorial"
_REGRAS = _COMPONENTES_CFG["regras"]
SELO_LARGURA_ALTA = Decimal(str(_REGRAS["selo_largura_alta"]))
SELO_LARGURA_MEDIA = Decimal(str(_REGRAS["selo_largura_media"]))
MIN_COMPONENTES_REAIS = int(_REGRAS["min_componentes_reais"])

# Fechamento em 100%: só o arredondamento da gravação. Valores derivados (peso x média somados
# empresa a empresa) acumulam o arredondamento de cada parcela, por isso a tolerância maior.
TOLERANCIA_FECHAMENTO = Decimal("0.000001")
TOLERANCIA_DERIVADA = Decimal("0.0001")

# Domínios das fontes permitidas na matriz de dados que podem aparecer como link (S-1).
DOMINIOS_DE_FONTE = (
    "sec.gov",
    "cvm.gov.br",
    "uspto.gov",
    "patentsview.org",
    "openalex.org",
    "ibge.gov.br",
    "gov.br",
    "bcb.gov.br",
    "opendatacommons.org",
)

# empresa_id do ADR 0005: CNPJ da companhia, CIK da SEC, LEI, ou "US:" + ticker enquanto a tabela
# ticker -> CIK da SEC não foi carregada (DT-3).
_EMPRESA_ID = re.compile(
    r"BR:CNPJ:(?P<cnpj>[A-Z0-9]{12}[0-9]{2})|US:CIK:[0-9]{10}|LEI:[A-Z0-9]{20}"
    r"|US:[A-Z]{1,5}(\.[A-Z])?"
)


def _numero(valor: Decimal) -> float:
    return float(valor)


# Fração de 0 a 1, em Decimal na validação e como número no JSON gravado.
Fracao = Annotated[
    Decimal,
    Field(ge=0, le=1),
    PlainSerializer(_numero, return_type=float, when_used="json"),
]


def _link_permitido(url: str) -> str:
    partes = urlsplit(url)
    host = (partes.hostname or "").lower()
    permitido = partes.scheme == "https" and any(
        host == dominio or host.endswith("." + dominio) for dominio in DOMINIOS_DE_FONTE
    )
    if not permitido:
        raise ValueError("link de fonte precisa ser https e de uma fonte permitida (S-1)")
    return url


LinkDeFonte = Annotated[str, AfterValidator(_link_permitido)]
IdFonte = Annotated[str, Field(pattern=r"^F[PA]-[0-9]{2}$")]


def _empresa_id_valido(valor: str) -> str:
    achado = _EMPRESA_ID.fullmatch(valor)
    if not achado or (achado.group("cnpj") and not cnpj_valido(achado.group("cnpj"))):
        raise ValueError("empresa_id fora dos formatos do ADR 0005")
    return valor


EmpresaId = Annotated[str, AfterValidator(_empresa_id_valido)]


def _perto(a: Decimal, b: Decimal, tolerancia: Decimal) -> bool:
    return abs(a - b) <= tolerancia


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _ComFaixa(_Base):
    media: Fracao
    p5: Fracao
    p95: Fracao

    @model_validator(mode="after")
    def _faixa_ordenada(self) -> _ComFaixa:
        if not self.p5 <= self.media <= self.p95:
            raise ValueError("a faixa precisa ter p5 <= media <= p95")
        return self


class Posicao(_Base):
    ticker: str
    nome: str
    tipo: Literal["acao", "etf"]
    peso: Fracao


class Carteira(_Base):
    id: Literal["big-techs", "sp500", "ibovespa"]
    nome: str
    descricao: str
    data_referencia: date
    posicoes: list[Posicao] = Field(min_length=1)

    @model_validator(mode="after")
    def _posicoes_fecham(self) -> Carteira:
        total = sum((p.peso for p in self.posicoes), Decimal(0))
        if not _perto(total, Decimal(1), TOLERANCIA_FECHAMENTO):
            raise ValueError(f"as posições da carteira somam {total}, e não 100%")
        return self


class Modelo(_Base):
    versao_irrae: str
    n_amostras: PositiveInt
    semente: int
    gerado_em: datetime
    # V-09 do ADR 0009: por ora, só o cenário de erros alinhados.
    cenario_faixa_carteira: Literal["comonotonico"]


class Cobertura(_Base):
    peso_com_irrae: Fracao
    peso_so_prior: Fracao
    peso_nao_coberto: Fracao


class Setor(_Base):
    id: str
    nome: str
    peso: Fracao


class Subtema(_ComFaixa):
    id: str
    nome: str


class Tema(_ComFaixa):
    id: str
    nome: str
    subtemas: list[Subtema]


class Exposicao(_Base):
    setores: list[Setor]
    temas: list[Tema]
    fora_do_tema: Fracao
    nao_coberto: Fracao


class Componente(_Base):
    id: str
    nome: str
    peso_p: Fracao
    presente: bool


class Folha(_ComFaixa):
    id: str
    nome: str


class Irrae(_Base):
    origem: Literal["irrae", "so_prior", "nao_coberto"]
    tema: str | None = None
    media: Fracao | None = None
    p5: Fracao | None = None
    p95: Fracao | None = None
    selo: Literal["alta", "media", "preliminar"] | None = None
    folhas: list[Folha] = []
    componentes: list[Componente] = []

    @model_validator(mode="after")
    def _coerente(self) -> Irrae:
        if self.origem == "nao_coberto":
            # Sem faixa inventada para quem não foi estimado (especificação, seção 5.3).
            if any(v is not None for v in (self.tema, self.media, self.p5, self.p95, self.selo)):
                raise ValueError("empresa não coberta não tem tema, faixa nem selo")
            if self.folhas or self.componentes:
                raise ValueError("empresa não coberta não tem folhas nem componentes")
            return self
        if None in (self.tema, self.media, self.p5, self.p95, self.selo):
            raise ValueError("empresa estimada precisa de tema, média, faixa e selo")
        assert self.media is not None and self.p5 is not None and self.p95 is not None  # noqa: S101
        if not self.p5 <= self.media <= self.p95:
            raise ValueError("a faixa precisa ter p5 <= media <= p95")
        self._confere_taxonomia()
        self._confere_componentes()
        self._confere_selo()
        return self

    def _confere_taxonomia(self) -> None:
        if self.tema not in _TAXONOMIA:
            raise ValueError(f"tema {self.tema} fora da taxonomia do IrRAE")
        folhas_do_tema = _TAXONOMIA[self.tema]["folhas"]
        for folha in self.folhas:
            if folhas_do_tema.get(folha.id) != folha.nome:
                raise ValueError(f"folha {folha.id} fora da taxonomia do tema {self.tema}")
        soma = sum((f.media for f in self.folhas), Decimal(0))
        if not _perto(soma, self.media or Decimal(0), TOLERANCIA_DERIVADA):
            raise ValueError("as médias das folhas não somam a média da empresa")

    def _confere_componentes(self) -> None:
        ids = [c.id for c in self.componentes]
        if sorted(ids) != sorted(COMPONENTES):
            raise ValueError(
                "os componentes precisam ser os da configuração do IrRAE, uma vez cada"
            )
        for c in self.componentes:
            if c.nome != COMPONENTES[c.id]:
                raise ValueError(f"nome do componente {c.id} difere da configuração")
            if not c.presente and c.peso_p != 0:
                raise ValueError(f"componente ausente {c.id} com peso p diferente de zero")
        soma = sum((c.peso_p for c in self.componentes if c.presente), Decimal(0))
        if not _perto(soma, Decimal(1), TOLERANCIA_DERIVADA):
            # Os pesos das fontes que faltam se redistribuem entre as presentes.
            raise ValueError("o peso p dos componentes presentes precisa somar 100%")

    def _confere_selo(self) -> None:
        # Mesma regra de irrae/regras.py (selo), com os limiares da configuração.
        if self.origem == "so_prior":
            esperado = "preliminar"
        else:
            reais = sum(1 for c in self.componentes if c.presente and c.id != COMPONENTE_PRIOR)
            larguras = [self.p95 - self.p5] + [f.p95 - f.p5 for f in self.folhas]  # type: ignore[operator]
            maior = max(larguras)
            if reais < MIN_COMPONENTES_REAIS:
                esperado = "preliminar"
            elif maior < SELO_LARGURA_ALTA:
                esperado = "alta"
            elif maior < SELO_LARGURA_MEDIA:
                esperado = "media"
            else:
                esperado = "preliminar"
        if self.selo != esperado:
            raise ValueError(f"selo {self.selo} não segue a largura da faixa (esperado {esperado})")


class FonteEmpresa(_Base):
    id: IdFonte
    descricao: str
    url: LinkDeFonte
    data: date


class Empresa(_Base):
    empresa_id: EmpresaId
    ticker: str
    nome: str
    pais: Literal["BR", "US"]
    peso_efetivo: Fracao
    caminho: list[str]
    setor: str
    irrae: Irrae
    fontes: list[FonteEmpresa]


class FonteCarteira(_Base):
    id: IdFonte
    descricao: str
    url: LinkDeFonte
    data_referencia: date


class Snapshot(_Base):
    """O snapshot de uma carteira da vitrine."""

    versao_schema: Literal["1"]
    # Verdadeiro nos snapshots de exemplo: o site mostra a faixa "Números ilustrativos".
    ilustrativo: bool
    carteira: Carteira
    modelo: Modelo
    cobertura: Cobertura
    exposicao: Exposicao
    empresas: list[Empresa]
    fontes_carteira: list[FonteCarteira]

    @model_validator(mode="after")
    def _fecha(self) -> Snapshot:
        self._confere_empresas()
        self._confere_cobertura()
        self._confere_exposicao()
        self._confere_temas()
        return self

    def _cobertas(self) -> list[Empresa]:
        return [e for e in self.empresas if e.irrae.origem != "nao_coberto"]

    def _confere_empresas(self) -> None:
        ids = [e.empresa_id for e in self.empresas]
        if len(ids) != len(set(ids)):
            raise ValueError("empresa repetida: classes da mesma empresa entram somadas")
        total = sum((e.peso_efetivo for e in self.empresas), Decimal(0))
        if total > 1 + TOLERANCIA_FECHAMENTO:
            raise ValueError(f"as empresas somam {total}, mais que 100% da carteira")

    def _confere_cobertura(self) -> None:
        c = self.cobertura
        total = c.peso_com_irrae + c.peso_so_prior + c.peso_nao_coberto
        if not _perto(total, Decimal(1), TOLERANCIA_FECHAMENTO):
            raise ValueError("a cobertura precisa fechar 100%")
        por_origem = {
            origem: sum(
                (e.peso_efetivo for e in self.empresas if e.irrae.origem == origem), Decimal(0)
            )
            for origem in ("irrae", "so_prior")
        }
        if not (
            _perto(c.peso_com_irrae, por_origem["irrae"], TOLERANCIA_DERIVADA)
            and _perto(c.peso_so_prior, por_origem["so_prior"], TOLERANCIA_DERIVADA)
        ):
            raise ValueError("a cobertura não bate com a origem do IrRAE de cada empresa")

    def _confere_exposicao(self) -> None:
        x = self.exposicao
        temas = sum((t.media for t in x.temas), Decimal(0))
        if not _perto(temas + x.fora_do_tema + x.nao_coberto, Decimal(1), TOLERANCIA_FECHAMENTO):
            raise ValueError("temas, fora do tema e não coberto não fecham 100%")
        coberto = sum((e.peso_efetivo for e in self._cobertas()), Decimal(0))
        # Não coberto = empresas sem estimativa e tudo o que não é empresa (caixa, derivativos).
        if not _perto(x.nao_coberto, 1 - coberto, TOLERANCIA_DERIVADA):
            raise ValueError("o não coberto não bate com as empresas cobertas")
        setores = sum((s.peso for s in x.setores), Decimal(0))
        if not _perto(setores, Decimal(1), TOLERANCIA_FECHAMENTO):
            raise ValueError("os setores precisam fechar 100%")

    def _confere_temas(self) -> None:
        for tema in self.exposicao.temas:
            if tema.id not in _TAXONOMIA or tema.nome != _TAXONOMIA[tema.id]["nome"]:
                raise ValueError(f"tema {tema.id} fora da taxonomia do IrRAE")
            empresas = [e for e in self._cobertas() if e.irrae.tema == tema.id]
            # Faixa comonotônica: os quantis se somam ponderados (irrae/agregacao.py).
            for campo in ("media", "p5", "p95"):
                esperado = sum(
                    (e.peso_efetivo * getattr(e.irrae, campo) for e in empresas), Decimal(0)
                )
                if not _perto(getattr(tema, campo), esperado, TOLERANCIA_DERIVADA):
                    nome = "média" if campo == "media" else campo
                    raise ValueError(f"{nome} do tema {tema.id} não bate com as empresas")
            folhas = _TAXONOMIA[tema.id]["folhas"]
            if [s.id for s in tema.subtemas] != list(folhas):
                raise ValueError(f"os subtemas do tema {tema.id} precisam seguir a taxonomia")
            for sub in tema.subtemas:
                if sub.nome != folhas[sub.id]:
                    raise ValueError(f"nome do subtema {sub.id} difere da taxonomia")
                for campo in ("media", "p5", "p95"):
                    esperado = sum(
                        (
                            e.peso_efetivo * getattr(f, campo)
                            for e in empresas
                            for f in e.irrae.folhas
                            if f.id == sub.id
                        ),
                        Decimal(0),
                    )
                    if not _perto(getattr(sub, campo), esperado, TOLERANCIA_DERIVADA):
                        raise ValueError(f"subtema {sub.id} não bate com as empresas ({campo})")
