"""Montagem da identificação e do setor oficial a partir das fontes da CVM (ADR 0008, etapa 4).

Junta quatro fontes, já lidas, nas linhas que a carga de cadastro grava (`cargas/cadastro.py`):

- **FCA** (`ingest/cvm_fca.py`): as companhias, o setor de cada uma, os tickers das ações e a raiz
  de cada ticker;
- **CDA** (`ingest/cvm_cda.py`), dos meses mais recentes: os pares ticker -> ISIN, as ações que os
  fundos têm e os tickers dos ETFs e FIIs emprestados;
- **informe de FII** (`ingest/cvm_fii.py`): ISIN, nome e tipo de cada FII;
- **curadoria manual** (`cargas/curadoria/`): o que as fontes não ligam sozinhas. Vale mais que
  elas.

Como cada ativo é identificado (ADR 0005):

- **Ação com ISIN:** toda ação brasileira que aparece no CDA (com ou sem ticker) fica pelo ISIN.
  A raiz do ISIN (3º ao 6º caractere) é o código do emissor na B3 e liga a ação à companhia pelo FCA
  ou pela curadoria. Sem companhia (ex.: BDR de empresa de fora, que não entrega FCA), a ação fica
  de fora e, no raio-x, aparece sem classificação. O ticker vem do par do CDA: no mesmo ticker ou
  ISIN em meses diferentes, vale o mês mais recente.
- **Ação só com ticker** (nenhum fundo a tem, então nenhuma fonte liberada traz o ISIN): o código
  interno `B3:` + ticker (decisão de 13/10/2026), ligado à companhia pelo FCA. Se um fundo comprar
  a ação, o CDA traz o ISIN e a carga seguinte passa a usá-lo sozinha.
- **ETF e FII:** pelo CNPJ da classe (`CNPJ:`). O ticker vem das cotas emprestadas no CDA ou da
  curadoria; o FII leva também o ISIN, o tipo e o segmento do informe mensal.

O setor de cada companhia é o setor de atividade do FCA, com o nome usado pela CVM (origem
"oficial"). A tradução para os setores do raio-x vem depois (ADR 0008, etapa 4).
"""

import csv
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from app.core.composicao import TipoItem
from app.core.identificadores import TICKER_B3, normalizar_cnpj
from cargas.rotina import ErroDeValidacao
from ingest.cvm_cda import MesCDA
from ingest.cvm_fca import CadastroFCA
from ingest.cvm_fii import InformesFII

_RAIZ = re.compile(r"[A-Z][A-Z0-9]{3}")


@dataclass(frozen=True, slots=True)
class Empresa:
    empresa_id: str  # "BR:CNPJ:" + CNPJ
    nome: str
    cnpj: str


@dataclass(frozen=True, slots=True)
class Ativo:
    ativo_id: str  # ISIN, "B3:" + ticker ou "CNPJ:" + CNPJ do fundo
    tipo: str  # "acao" ou "fundo"
    empresa_id: str | None  # só nas ações
    ticker_b3: str | None
    isin: str | None
    nome: str | None
    fii_tipo: str | None = None  # só nos FIIs
    fii_segmento: str | None = None  # só no FII de tijolo com segmento


@dataclass(frozen=True, slots=True)
class Setor:
    empresa_id: str
    setor: str  # setor de atividade, com o nome usado pela CVM


@dataclass(frozen=True, slots=True)
class Identificacao:
    empresas: list[Empresa]
    ativos: list[Ativo]
    setores: list[Setor]
    descartes: Counter[str]  # o que ficou de fora, por motivo; nunca o conteúdo


@dataclass(frozen=True, slots=True)
class Curadoria:
    emissores: dict[str, tuple[str, str]]  # raiz -> (CNPJ, nome da companhia)
    fundos_listados: dict[str, str]  # ticker de ETF ou FII -> CNPJ do fundo


def montar(
    fca: CadastroFCA,
    meses: list[MesCDA],
    fiis: InformesFII,
    curadoria: Curadoria,
) -> Identificacao:
    """Monta a identificação. `meses` vem do mais recente para o mais antigo."""
    descartes: Counter[str] = Counter()
    empresas = {
        cnpj: Empresa(f"BR:CNPJ:{cnpj}", c.nome, cnpj) for cnpj, c in fca.companhias.items()
    }
    for cnpj, nome in curadoria.emissores.values():
        empresas.setdefault(cnpj, Empresa(f"BR:CNPJ:{cnpj}", nome, cnpj))
    # A curadoria vale mais que o FCA: é a correção revisada à mão.
    cnpj_da_raiz = fca.cnpj_da_raiz | {r: cnpj for r, (cnpj, _) in curadoria.emissores.items()}

    ativos: dict[str, Ativo] = {}
    tickers_usados: set[str] = set()

    # Ações com ISIN: os pares do CDA (o mês mais recente primeiro, um ticker para cada ISIN) e
    # todas as ações brasileiras das composições.
    ticker_do_isin: dict[str, str] = {}
    for mes in meses:
        for ticker, isin in mes.isin_do_ticker.items():
            novo = ticker not in tickers_usados and isin not in ticker_do_isin
            if novo and TICKER_B3.fullmatch(ticker):
                ticker_do_isin[isin] = ticker
                tickers_usados.add(ticker)
    for isin in sorted(set(ticker_do_isin) | _isins_das_composicoes(meses)):
        cnpj = cnpj_da_raiz.get(isin[2:6])
        if cnpj is None:
            descartes["acao_sem_companhia"] += 1
            continue
        ticker = ticker_do_isin.get(isin)
        ativos[isin] = Ativo(isin, "acao", f"BR:CNPJ:{cnpj}", ticker, isin, ticker)

    # Ações só com ticker: o código interno da B3.
    for ticker, cnpj_do_fca in sorted(fca.cnpj_do_ticker.items()):
        if ticker in tickers_usados:
            continue
        cnpj = cnpj_da_raiz.get(ticker[:4], cnpj_do_fca)
        ativos[f"B3:{ticker}"] = Ativo(
            f"B3:{ticker}", "acao", f"BR:CNPJ:{cnpj}", ticker, None, ticker
        )
        tickers_usados.add(ticker)

    # Fundos listados (ETF e FII) com ticker: o CDA, do mês mais recente para o mais antigo, e
    # por cima a curadoria.
    cnpj_do_listado: dict[str, str] = {}
    for mes in reversed(meses):
        cnpj_do_listado |= mes.cnpj_do_fundo_listado
    cnpj_do_listado |= curadoria.fundos_listados
    ticker_do_fundo: dict[str, str] = {}
    for ticker, cnpj in sorted(cnpj_do_listado.items()):
        if ticker in tickers_usados:
            descartes["ticker_de_fundo_repetido"] += 1
            continue
        ticker_do_fundo.setdefault(cnpj, ticker)
        tickers_usados.add(ticker)

    # ISIN informado por mais de um FII (caso real: classes diferentes com o mesmo ISIN) ou já usado
    # por uma ação: não dá para saber de quem é, e nenhum fica com ele.
    vezes = Counter(f.isin for f in fiis.fundos.values() if f.isin)
    isins_das_acoes = {a.isin for a in ativos.values() if a.isin}
    ambiguos = {i for i, n in vezes.items() if n > 1 or i in isins_das_acoes}
    descartes["isin_de_fii_ambiguo"] += len(ambiguos)
    nomes = _nomes_dos_fundos(meses)
    for cnpj in sorted(set(ticker_do_fundo) | set(fiis.fundos)):
        fii = fiis.fundos.get(cnpj)
        isin = fii.isin if fii and fii.isin not in ambiguos else None
        ativos[f"CNPJ:{cnpj}"] = Ativo(
            ativo_id=f"CNPJ:{cnpj}",
            tipo="fundo",
            empresa_id=None,
            ticker_b3=ticker_do_fundo.get(cnpj),
            isin=isin,
            nome=fii.nome if fii else nomes.get(f"CNPJ:{cnpj}"),
            fii_tipo=fii.tipo.value if fii else None,
            fii_segmento=fii.segmento if fii else None,
        )

    setores = [
        Setor(f"BR:CNPJ:{cnpj}", c.setor) for cnpj, c in sorted(fca.companhias.items()) if c.setor
    ]
    return Identificacao(
        empresas=sorted(empresas.values(), key=lambda e: e.empresa_id),
        ativos=sorted(ativos.values(), key=lambda a: a.ativo_id),
        setores=setores,
        descartes=+descartes,
    )


def _isins_das_composicoes(meses: Iterable[MesCDA]) -> set[str]:
    """Os ISINs das ações nas composições (os itens americanos, "US:", ficam de fora)."""
    return {
        item.ativo_id
        for mes in meses
        for composicao in mes.composicoes.values()
        for item in composicao.itens
        if item.tipo is TipoItem.ACAO and item.ativo_id and not item.ativo_id.startswith("US:")
    }


def _nomes_dos_fundos(meses: list[MesCDA]) -> dict[str, str]:
    """O nome de cada fundo como a CVM informa no CDA; no mais recente, vale o dele."""
    nomes: dict[str, str] = {}
    for mes in reversed(meses):
        nomes |= mes.nomes
    return nomes


# --- Curadoria manual (cargas/curadoria/README.md) ---


class CuradoriaInvalida(ErroDeValidacao, ValueError):
    """Linha errada num arquivo da curadoria. A mensagem diz o arquivo, a linha e o que está errado,
    nunca o conteúdo, e vai para o motivo da carga (cargas/rotina.motivo)."""


def ler_curadoria(pasta: Path) -> Curadoria:
    """Lê e confere os arquivos de curadoria. Uma linha errada levanta CuradoriaInvalida com o
    arquivo e a linha: a carga para, em vez de gravar uma ligação errada."""
    emissores: dict[str, tuple[str, str]] = {}
    for n, linha in _linhas(pasta / "emissores_b3.csv", ("raiz", "cnpj", "nome", "motivo")):
        onde = f"emissores_b3.csv, linha {n}"
        raiz = linha["raiz"].strip()
        if not _RAIZ.fullmatch(raiz):
            raise CuradoriaInvalida(
                f"{onde}: raiz fora do formato (4 caracteres, começando por letra)"
            )
        if raiz in emissores:
            raise CuradoriaInvalida(f"{onde}: raiz repetida")
        emissores[raiz] = (_cnpj(linha["cnpj"], onde), linha["nome"].strip())
    fundos: dict[str, str] = {}
    for n, linha in _linhas(pasta / "fundos_listados.csv", ("ticker", "cnpj", "nome", "fonte")):
        onde = f"fundos_listados.csv, linha {n}"
        ticker = linha["ticker"].strip()
        if not TICKER_B3.fullmatch(ticker):
            raise CuradoriaInvalida(f"{onde}: ticker fora do formato da B3")
        if ticker in fundos:
            raise CuradoriaInvalida(f"{onde}: ticker repetido")
        fundos[ticker] = _cnpj(linha["cnpj"], onde)
    return Curadoria(emissores=emissores, fundos_listados=fundos)


def _linhas(caminho: Path, colunas: tuple[str, ...]) -> Iterable[tuple[int, dict[str, str]]]:
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        if tuple(leitor.fieldnames or ()) != colunas:
            raise CuradoriaInvalida(f"{caminho.name}: o cabeçalho precisa ser {';'.join(colunas)}")
        # A linha 1 é o cabeçalho: a primeira linha de dados é a 2.
        yield from enumerate(leitor, start=2)


def _cnpj(texto: str, onde: str) -> str:
    try:
        return normalizar_cnpj(texto)
    except ValueError:
        raise CuradoriaInvalida(f"{onde}: CNPJ inválido") from None
