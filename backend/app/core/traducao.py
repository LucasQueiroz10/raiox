"""Do identificador de cada posição ao ativo_id (ADR 0005, seção 5).

A carteira chega pelo ISIN, pelo ticker da B3, pelo ticker americano ou pelo CNPJ do fundo, já
validado e normalizado (app/core/identificadores). A tradução usa a identificação vigente, montada
pela carga do cadastro (ref.ativo_vigente; cargas/identificacao.py):

- **isin:** o ativo registrado com esse ISIN. O ISIN de um FII vira o CNPJ do fundo; o de uma ação
  ou de um ETF UCITS é o próprio ativo_id.
- **ticker_b3:** o ativo registrado com esse ticker (ISIN, código interno "B3:" ou o CNPJ do ETF ou
  FII). Sem ticker registrado, o FII é achado pela raiz do ISIN (o 3º ao 6º caractere do ISIN
  brasileiro são os 4 primeiros do ticker), se um FII só tiver essa raiz: a carga só conhece o
  ticker dos FIIs que aparecem emprestados no CDA ou na curadoria. Senão, "B3:" + ticker.
- **ticker_eua:** o ativo registrado, ou "US:" + ticker.
- **cnpj:** "CNPJ:" + CNPJ (fundos brasileiros sempre pelo CNPJ).

Identificador válido e desconhecido continua entrando: o próprio ativo_id faz o papel da empresa,
sem classificação.

O tipo (ação ou fundo) do ativo conhecido vem da identificação; o que a pessoa declarou só vale
para o identificador desconhecido (decisão do Lucas, 14/10/2026). Assim, um FII marcado como ação
não vira uma empresa sem classificação, e uma ação marcada como fundo não vira "não aberto".
"""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from app.core.composicao import ClasseFii, TipoItem

type TipoIdentificador = Literal["isin", "ticker_b3", "ticker_eua", "cnpj"]


@dataclass(frozen=True, slots=True)
class AtivoIdentificado:
    """Um ativo da identificação vigente, só com o que a tradução usa."""

    ativo_id: str
    tipo: TipoItem  # ACAO ou FUNDO
    ticker_b3: str | None = None
    ticker_eua: str | None = None
    isin: str | None = None
    # Só nos FIIs: o tipo e o segmento. Entra na busca pela raiz do ISIN e no raio-x.
    fii: ClasseFii | None = None


@dataclass(frozen=True, slots=True)
class TabelaIdentificacao:
    """Os índices da tradução, montados uma vez por foto dos dados."""

    ativo_do_ticker_b3: Mapping[str, str]
    ativo_do_ticker_eua: Mapping[str, str]
    ativo_do_isin: Mapping[str, str]
    fii_da_raiz: Mapping[str, str]  # só as raízes de um FII só
    tipo_do_ativo: Mapping[str, TipoItem]
    classe_do_fii: Mapping[str, ClasseFii]  # para o raio-x mostrar os FIIs pelo tipo

    @classmethod
    def montar(cls, ativos: Iterable[AtivoIdentificado]) -> TabelaIdentificacao:
        """Monta os índices; lança ValueError se um ticker ou ISIN aparecer em dois ativos (o
        banco já não deixa, numa mesma carga; o conjunto de exemplo é conferido aqui)."""
        ativos = list(ativos)
        indices: dict[str, dict[str, str]] = {"ticker_b3": {}, "ticker_eua": {}, "isin": {}}
        for a in ativos:
            for campo, indice in indices.items():
                valor = getattr(a, campo)
                if valor is None:
                    continue
                if valor in indice:
                    raise ValueError(f"{campo} repetido na identificação")
                indice[valor] = a.ativo_id
        raizes = Counter(a.isin[2:6] for a in ativos if a.fii is not None and a.isin)
        return cls(
            ativo_do_ticker_b3=indices["ticker_b3"],
            ativo_do_ticker_eua=indices["ticker_eua"],
            ativo_do_isin=indices["isin"],
            fii_da_raiz={
                a.isin[2:6]: a.ativo_id
                for a in ativos
                if a.fii is not None and a.isin and raizes[a.isin[2:6]] == 1
            },
            tipo_do_ativo={a.ativo_id: a.tipo for a in ativos},
            classe_do_fii={a.ativo_id: a.fii for a in ativos if a.fii is not None},
        )


def _ativo_id(
    tipo_identificador: TipoIdentificador, identificador: str, t: TabelaIdentificacao
) -> str:
    match tipo_identificador:
        case "isin":
            return t.ativo_do_isin.get(identificador, identificador)
        case "ticker_b3":
            if ativo := t.ativo_do_ticker_b3.get(identificador):
                return ativo
            return t.fii_da_raiz.get(identificador[:4], f"B3:{identificador}")
        case "ticker_eua":
            return t.ativo_do_ticker_eua.get(identificador, f"US:{identificador}")
        case "cnpj":
            return f"CNPJ:{identificador}"
        case _:
            # O esquema da API só aceita os tipos acima; um tipo novo sem tradução não pode virar
            # um ativo vazio em silêncio.
            raise ValueError("tipo de identificador sem tradução")


def traduzir(
    tipo_identificador: TipoIdentificador,
    identificador: str,
    tipo_declarado: TipoItem,
    tabela: TabelaIdentificacao,
) -> tuple[str, TipoItem]:
    """O ativo_id e o tipo da posição. `identificador` já vem normalizado."""
    ativo_id = _ativo_id(tipo_identificador, identificador, tabela)
    return ativo_id, tabela.tipo_do_ativo.get(ativo_id, tipo_declarado)
