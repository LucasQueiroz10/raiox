"""Leitor do CDA da CVM: lê o zip de um mês e devolve as composições dos fundos (ADR 0008).

Sem banco e sem rede: a carga (etapa 3) baixa o zip e grava o resultado. As regras de tradução
estão nas seções 1 a 4 do ADR 0008. O CPF de emissor pessoa física nunca sai daqui: o leitor só
aproveita o emissor quando ele é pessoa jurídica e tem um CNPJ válido.

Arquivos em latin-1, separador `;`, números com ponto decimal. Lidos com `csv` e `Decimal`,
nunca `float`. Um arquivo, uma coluna ou um tipo de aplicação fora do esperado para a leitura
(LayoutInesperado): a carga não publica e avisa (pedido do M1).
"""

import re
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path
from typing import IO

from app.core.composicao import Composicao, ItemComposicao, TipoItem
from app.core.identificadores import isin_valido
from app.core.lookthrough import PRECISAO
from ingest import arquivos_cvm
from ingest.arquivos_cvm import LayoutInesperado, linhas_csv

FONTE = "CVM (CDA)"

_COMUNS = (
    "TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE", "DENOM_SOCIAL", "DT_COMPTC", "TP_APLIC", "TP_ATIVO",
    "EMISSOR_LIGADO", "TP_NEGOC", "QT_VENDA_NEGOC", "VL_VENDA_NEGOC", "QT_AQUIS_NEGOC",
    "VL_AQUIS_NEGOC", "QT_POS_FINAL", "VL_MERC_POS_FINAL", "VL_CUSTO_POS_FINAL", "DT_CONFID_APLIC",
)  # fmt: skip
_RENDA_FIXA = (
    "DT_VENC", "TITULO_POSFX", "CD_INDEXADOR_POSFX", "DS_INDEXADOR_POSFX", "PR_INDEXADOR_POSFX",
    "PR_CUPOM_POSFX", "PR_TAXA_PREFX",
)  # fmt: skip
_RISCO = ("RISCO_EMISSOR", "AG_RISCO", "DT_RISCO", "GRAU_RISCO")
_CONFID = (
    "TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE", "DENOM_SOCIAL", "DT_COMPTC", "TP_APLIC",
    "VL_VENDA_NEGOC", "VL_AQUIS_NEGOC", "VL_MERC_POS_FINAL", "VL_CUSTO_POS_FINAL",
    "DT_CONFID_APLIC",
)  # fmt: skip

# Colunas de cada arquivo do mês, como a CVM publica (conferidas no mês de agosto de 2026).
COLUNAS: dict[str, tuple[str, ...]] = {
    "fi_PL": ("TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE", "DENOM_SOCIAL", "DT_COMPTC", "VL_PATRIM_LIQ"),
    "fi_BLC_1": (*_COMUNS, "TP_TITPUB", "CD_ISIN", "CD_SELIC", "DT_EMISSAO", "DT_VENC"),
    "fi_BLC_2": (
        *_COMUNS, "CNPJ_FUNDO_CLASSE_COTA", "ID_SUBCLASSE", "NM_FUNDO_CLASSE_SUBCLASSE_COTA",
    ),
    "fi_BLC_3": (*_COMUNS, "CD_SWAP", "DS_SWAP"),
    "fi_BLC_4": (*_COMUNS, "CD_ATIVO", "DS_ATIVO", "CD_ISIN", "DT_INI_VIGENCIA", "DT_FIM_VIGENCIA"),
    "fi_BLC_5": (*_COMUNS, "CNPJ_EMISSOR", "EMISSOR", *_RENDA_FIXA, *_RISCO),
    "fi_BLC_6": (
        *_COMUNS, "PF_PJ_EMISSOR", "CPF_CNPJ_EMISSOR", "EMISSOR", *_RENDA_FIXA, "TITULO_CETIP",
        "TITULO_GARANTIA", "CNPJ_INSTITUICAO_FINANC_COOBR",
    ),
    "fi_BLC_7": (
        *_COMUNS, "INVEST_COLETIVO", "INVEST_COLETIVO_GESTOR", "EMISSOR", "DT_VENC", "CD_PAIS",
        "PAIS", "CD_BV_MERC", "BV_MERC", "CD_ATIVO_BV_MERC", *_RISCO, "DS_ATIVO_EXTERIOR",
        "QT_ATIVO_EXTERIOR", "VL_ATIVO_EXTERIOR",
    ),
    "fi_BLC_8": (*_COMUNS, "DS_ATIVO", "PF_PJ_EMISSOR", "CPF_CNPJ_EMISSOR", "EMISSOR"),
    "fi_CONFID": _CONFID,
    # ETFs, FIDCs e FIAGROs, com o patrimônio em cada linha (antes de 15/11/2025: cda_fiim).
    "fie": (
        "TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE", "DENOM_SOCIAL", "DT_COMPTC", "ID_DOC",
        "VL_PATRIM_LIQ", *_COMUNS[4:], "CD_ATIVO", "DS_ATIVO", "DT_VENC", "PF_PJ_EMISSOR",
        "CPF_CNPJ_EMISSOR", "EMISSOR", "RISCO_EMISSOR", "CD_SELIC", "DT_INI_VIGENCIA", "CD_PAIS",
        "PAIS", "CD_BV_MERC", "BV_MERC",
    ),
    "fie_CONFID": (*_CONFID[:4], "ID_DOC", *_CONFID[4:]),
}  # fmt: skip

# Ordem de leitura: o patrimônio antes das aplicações e o bloco de ações (pares ticker -> ISIN)
# antes do arquivo dos ETFs.
_APLICACOES = tuple(f"fi_BLC_{n}" for n in range(1, 9)) + ("fie",)
_CONFIDENCIAIS = ("fi_CONFID", "fie_CONFID")

# Países de ISIN que podem ser guardados: a mesma lista do domínio ref.ativo_id (ADR 0005). ZZ não
# é país: é o prefixo dos ISINs sintéticos dos testes.
_PAISES_ISIN = ("BR", "IE", "LU", "ZZ")
# Bolsas americanas pelo código da CVM: AMEX, Nasdaq e NYSE.
_BOLSAS_EUA = frozenset({"A1", "A11", "A12"})
# Ticker americano, sozinho ou com o código da bolsa (ex.: "AAPL", "AAPL US", "BRK.B UN").
_TICKER_EUA = re.compile(r"([A-Z]{1,5}(?:\.[A-Z])?)(?: U[A-Z])?")

_ACAO, _FUNDO, _CAIXA = TipoItem.ACAO, TipoItem.FUNDO, TipoItem.CAIXA
_DERIVATIVO, _CREDITO, _OUTRO = TipoItem.DERIVATIVO, TipoItem.CREDITO, TipoItem.OUTRO

# Tipo de aplicação -> (tipo do motor, passivo). O CDA informa os passivos com valor positivo, e o
# leitor troca o sinal (ADR 0008, seção 4).
_TRADUCAO: dict[str, tuple[TipoItem, bool]] = {
    "Títulos Públicos": (TipoItem.TITULO_PUBLICO, False),
    "Operações Compromissadas": (_CAIXA, False),
    "Disponibilidades": (_CAIXA, False),
    "Valores a receber": (_CAIXA, False),
    "Valores a pagar": (_CAIXA, True),
    "Outras operações passivas e exigibilidades": (_CAIXA, True),
    "Cotas de Fundos": (_FUNDO, False),
    "Cotas de fundos de investimento - Instrução Nº 409": (_FUNDO, False),
    "Ações": (_ACAO, False),
    "Ações e outros TVM cedidos em empréstimo": (_ACAO, False),
    "Obrigações por ações e outros TVM recebidos em empréstimo": (_ACAO, True),
    "Certificado ou recibo de depósito de valores mobiliários": (_ACAO, False),
    "Brazilian Depository Receipt - BDR": (_ACAO, False),
    "Debêntures": (_CREDITO, False),
    "Depósitos a prazo e outros títulos de IF": (_CREDITO, False),
    "Títulos ligados ao agronegócio": (_CREDITO, False),
    "Títulos de Crédito Privado": (_CREDITO, False),
    "Opções - Posições titulares": (_DERIVATIVO, False),
    "Opções - Posições lançadas": (_DERIVATIVO, True),
    "Mercado Futuro - Posições compradas": (_DERIVATIVO, False),
    "Mercado Futuro - Posições vendidas": (_DERIVATIVO, False),
    "DIFERENCIAL DE SWAP A RECEBER": (_DERIVATIVO, False),
    "DIFERENCIAL DE SWAP A PAGAR": (_DERIVATIVO, True),
    "Compras a termo a receber": (_DERIVATIVO, False),
    "Vendas a termo a receber": (_DERIVATIVO, False),
    "Obrigações por compra a termo a pagar": (_DERIVATIVO, True),
    "Obrigações por venda a termo a entregar": (_DERIVATIVO, True),
    "Outras aplicações": (_OUTRO, False),
    "Outros valores mobiliários registrados na CVM objeto de oferta pública": (_OUTRO, False),
    "Outros valores mobiliários ofertados privadamente": (_OUTRO, False),
    "Investimento no Exterior": (_OUTRO, False),  # o tipo vem do tipo de ativo (abaixo)
}
_EXTERIOR = "Investimento no Exterior"
_NO_EXTERIOR: dict[str, TipoItem] = {
    "Ação ordinária": _ACAO,
    "Ação preferencial": _ACAO,
    "Depository Receipt no Exterior(DR)": _ACAO,
    "Fundos Offshore": _FUNDO,
    "Opção de compra": _DERIVATIVO,
    "Opção de venda": _DERIVATIVO,
    "SWAP": _DERIVATIVO,
    "Título da Dívida Externa": TipoItem.TITULO_PUBLICO,
    "Bonds e Treasury": _OUTRO,
    "Outros": _OUTRO,
}
# Tipos de ativo que mudam o tipo da aplicação: cota de fundo numa linha de ação (ex.: ETF
# emprestado), recibo de subscrição, títulos de crédito e derivativos em "outros".
_ATIVO_E_FUNDO = frozenset(
    {"Fundos de Índice", "FI Imobiliário", "Fundo de Investimento e de Cotas", "BDR de ETF"}
)
_POR_TIPO_DE_ATIVO: dict[str, TipoItem] = {
    "Recibo de subscrição": _OUTRO,
    "Bônus de subscrição": _OUTRO,
    "Certificado de recebíveis imobiliários": _CREDITO,
    "Nota Promissória/ Commercial Paper/ Export Note": _CREDITO,
    "Outros instrumentos derivativos": _DERIVATIVO,
}
_MUDA_PELO_ATIVO = (_ACAO, _OUTRO)
# Cotas de fundos negociados em bolsa (ETF e FII) emprestadas, no bloco 8: a descrição traz o ticker
# (ex.: "BOVA11 - ETF") e o emissor é o próprio fundo. É a única fonte liberada que liga o ticker
# de um ETF ou FII ao CNPJ (ADR 0008, etapa 4).
_FUNDO_LISTADO = frozenset({"Fundos de Índice", "FI Imobiliário"})
_TICKER_NA_DESCRICAO = re.compile(r"([A-Z][A-Z0-9]{3}[0-9]{2})\b")


@dataclass(frozen=True, slots=True)
class MesCDA:
    composicoes: dict[str, Composicao]  # por fundo_id ("CNPJ:" + CNPJ da classe)
    nomes: dict[str, str]  # nome do fundo como a CVM informa
    # Peso líquido da parte confidencial de cada fundo (ADR 0008, seção 3), fora das composições.
    confidencial: dict[str, Decimal]
    # Patrimônio zero, negativo ou ausente: sem composição, mas com aviso na tela.
    sem_composicao_utilizavel: frozenset[str]
    # Soma de todas as linhas de cada fundo ÷ patrimônio, para o relatório da carga (verificação a).
    soma_das_linhas: dict[str, Decimal]
    isin_do_ticker: dict[str, str]  # pares do bloco de ações, sem os tickers com dois ISINs
    # Ticker de ETF ou FII -> CNPJ do fundo (cotas emprestadas), sem os tickers com dois CNPJs.
    cnpj_do_fundo_listado: dict[str, str]
    descartes: Counter[str]  # linhas (ou fundos) deixados de fora, por motivo; nunca o conteúdo
    # Para auditar e recalcular (ADR 0006, seção 4): o patrimônio de cada fundo com composição e o
    # valor em reais de cada item, na mesma ordem dos itens, com o sinal da seção 4 do ADR 0008.
    patrimonio: dict[str, Decimal]
    valores: dict[str, tuple[Decimal, ...]]


def nome_do_arquivo(arquivo: str, mes: str) -> str:
    """Nome do arquivo dentro do zip, ex.: ("fi_BLC_4", "202608") -> cda_fi_BLC_4_202608.csv."""
    return f"cda_{arquivo}_{mes}.csv"


def ler_mes(origem: Path | IO[bytes]) -> MesCDA:
    """Lê o zip de um mês do CDA (ex.: cda_fi_202608.zip)."""
    with zipfile.ZipFile(origem) as z:
        mes = _mes_do_zip(z.namelist())
        leitor = _Leitor()
        leitor.ler_patrimonio(_linhas(z, "fi_PL", mes))
        for arquivo in _APLICACOES:
            leitor.ler_aplicacoes(arquivo, _linhas(z, arquivo, mes))
        for arquivo in _CONFIDENCIAIS:
            leitor.ler_confidencial(_linhas(z, arquivo, mes))
    return leitor.resultado()


def _mes_do_zip(nomes: list[str]) -> str:
    achados = {m.group(1) for n in nomes if (m := re.fullmatch(r"cda_fi_PL_(\d{6})\.csv", n))}
    if len(achados) != 1:
        raise LayoutInesperado("o zip precisa ter um arquivo de patrimônio (cda_fi_PL_AAAAMM.csv)")
    mes = achados.pop()
    esperados = {nome_do_arquivo(a, mes) for a in COLUNAS}
    faltam, sobram = sorted(esperados - set(nomes)), sorted(set(nomes) - esperados)
    if faltam or sobram:
        raise LayoutInesperado(f"arquivos fora do esperado: faltam {faltam}; sobram {sobram}")
    return mes


def _linhas(z: zipfile.ZipFile, arquivo: str, mes: str) -> Iterator[dict[str, str]]:
    return linhas_csv(z, nome_do_arquivo(arquivo, mes), COLUNAS[arquivo])


def _traduzir(tp_aplic: str, tp_ativo: str) -> tuple[TipoItem, bool]:
    if tp_aplic not in _TRADUCAO:
        raise LayoutInesperado(f"tipo de aplicação desconhecido: {tp_aplic!r}")
    tipo, passivo = _TRADUCAO[tp_aplic]
    if tp_aplic == _EXTERIOR:
        return _NO_EXTERIOR.get(tp_ativo, _OUTRO), passivo
    if tipo in _MUDA_PELO_ATIVO:
        if tp_ativo in _ATIVO_E_FUNDO:
            return _FUNDO, passivo
        return _POR_TIPO_DE_ATIVO.get(tp_ativo, tipo), passivo
    return tipo, passivo


# Chave de um item da composição: (tipo, ativo_id, empresa_id, emissor). Linhas com a mesma chave
# somam: a ação emprestada que o fundo ainda tem anula a obrigação de devolvê-la.
type _Chave = tuple[TipoItem, str | None, str | None, str | None]


@dataclass(slots=True)
class _Fundo:
    data: date | None = None
    patrimonio: Decimal | None = None
    nome: str = ""
    soma: Decimal = Decimal(0)
    confidencial: Decimal = Decimal(0)
    tem_linhas: bool = False


class _Leitor:
    def __init__(self) -> None:
        self.fundos: dict[str, _Fundo] = defaultdict(_Fundo)
        self.valores: dict[str, dict[_Chave, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
        self.pares: dict[str, set[str]] = defaultdict(set)
        self.fundos_listados: dict[str, set[str]] = defaultdict(set)
        self.descartes: Counter[str] = Counter()

    def _fundo(self, linha: dict[str, str]) -> tuple[str, _Fundo] | None:
        cnpj = arquivos_cvm.cnpj(linha["CNPJ_FUNDO_CLASSE"])
        if cnpj is None:
            self.descartes["cnpj_do_fundo_invalido"] += 1
            return None
        return cnpj, self.fundos[cnpj]

    def ler_patrimonio(self, linhas: Iterator[dict[str, str]]) -> None:
        for linha in linhas:
            achado = self._fundo(linha)
            if achado is None:
                continue
            _, fundo = achado
            self._guardar_patrimonio(fundo, linha)

    def _guardar_patrimonio(self, fundo: _Fundo, linha: dict[str, str]) -> None:
        fundo.patrimonio = arquivos_cvm.valor(linha["VL_PATRIM_LIQ"])
        fundo.nome = linha["DENOM_SOCIAL"].strip()
        try:
            fundo.data = date.fromisoformat(linha["DT_COMPTC"].strip())
        except ValueError:
            fundo.data = None
            self.descartes["data_invalida"] += 1

    def ler_aplicacoes(self, arquivo: str, linhas: Iterator[dict[str, str]]) -> None:
        for linha in linhas:
            achado = self._fundo(linha)
            if achado is None:
                continue
            cnpj, fundo = achado
            if arquivo == "fie" and fundo.patrimonio is None:
                self._guardar_patrimonio(fundo, linha)
            tipo, passivo = _traduzir(linha["TP_APLIC"].strip(), linha["TP_ATIVO"].strip())
            if arquivo == "fi_BLC_8":
                self._guardar_fundo_listado(linha)
            valor = self._somar(fundo, linha, passivo)
            if valor is None:
                continue
            chave = self._chave(arquivo, tipo, linha)
            if chave is None:
                self.descartes["acao_sem_identificacao"] += 1
                continue
            self.valores[cnpj][chave] += valor

    def _guardar_fundo_listado(self, linha: dict[str, str]) -> None:
        """Guarda o par ticker -> CNPJ de uma cota de ETF ou FII. Só pessoa jurídica: o campo do
        emissor pessoa física (CPF) nunca é lido."""
        if linha["TP_ATIVO"].strip() not in _FUNDO_LISTADO:
            return
        if linha["PF_PJ_EMISSOR"].strip() != "PJ":
            return
        ticker = _TICKER_NA_DESCRICAO.match(linha["DS_ATIVO"].strip().upper())
        cnpj = arquivos_cvm.cnpj(linha["CPF_CNPJ_EMISSOR"])
        if ticker and cnpj:
            self.fundos_listados[ticker.group(1)].add(cnpj)

    def ler_confidencial(self, linhas: Iterator[dict[str, str]]) -> None:
        for linha in linhas:
            achado = self._fundo(linha)
            if achado is None:
                continue
            _, fundo = achado
            _, passivo = _traduzir(linha["TP_APLIC"].strip(), "")
            valor = self._somar(fundo, linha, passivo)
            if valor is not None:
                fundo.confidencial += valor

    def _somar(self, fundo: _Fundo, linha: dict[str, str], passivo: bool) -> Decimal | None:
        """O valor da linha com o sinal certo, já somado ao fundo; None se for inválido. O fundo
        com linha fica com composição, mesmo que nenhuma linha seja aproveitada."""
        fundo.tem_linhas = True
        valor = arquivos_cvm.valor(linha["VL_MERC_POS_FINAL"])
        if valor is None:
            self.descartes["valor_invalido"] += 1
            return None
        valor = -valor if passivo else valor
        fundo.soma += valor
        return valor

    def _chave(self, arquivo: str, tipo: TipoItem, linha: dict[str, str]) -> _Chave | None:
        """A chave do item, ou None para a ação que não dá para identificar."""
        if tipo is _ACAO:
            return self._acao(arquivo, linha)
        if tipo is _FUNDO:
            return (_FUNDO, self._cota(arquivo, linha), None, None)
        if tipo is _CREDITO:
            # DT-13: as debêntures do bloco de ações não trazem o emissor e ficam sem empresa.
            return (_CREDITO, None, None, self._emissor(arquivo, linha))
        # DT-14: derivativos sem o ativo-objeto.
        return (tipo, None, None, None)

    def _acao(self, arquivo: str, linha: dict[str, str]) -> _Chave | None:
        if linha["TP_APLIC"].strip() == _EXTERIOR:
            codigo = linha["CD_ATIVO_BV_MERC" if arquivo == "fi_BLC_7" else "CD_ATIVO"]
            ticker = _TICKER_EUA.fullmatch(codigo.strip().upper())
            if linha["CD_BV_MERC"].strip() in _BOLSAS_EUA and ticker:
                return (_ACAO, "US:" + ticker.group(1), None, None)
            return None
        if arquivo == "fi_BLC_4":
            isin = linha["CD_ISIN"].strip().upper()
            if not (isin_valido(isin) and isin.startswith(_PAISES_ISIN)):
                return None
            ticker = linha["CD_ATIVO"].strip().upper()
            if ticker:
                self.pares[ticker].add(isin)
            return (_ACAO, isin, None, None)
        if arquivo == "fie":
            isins = self.pares.get(linha["CD_ATIVO"].strip().upper(), set())
            if len(isins) == 1:
                return (_ACAO, next(iter(isins)), None, None)
        empresa = self._emissor(arquivo, linha)
        return (_ACAO, None, empresa, None) if empresa else None

    def _cota(self, arquivo: str, linha: dict[str, str]) -> str | None:
        if arquivo == "fi_BLC_2":
            cnpj = arquivos_cvm.cnpj(linha["CNPJ_FUNDO_CLASSE_COTA"])
        elif arquivo == "fie" and linha["PF_PJ_EMISSOR"].strip() == "PJ":
            # O arquivo dos ETFs não tem a coluna da classe investida: vale o CNPJ do emissor da
            # cota. Se não for o de uma classe com composição, a tela avisa "fundo sem composição".
            cnpj = arquivos_cvm.cnpj(linha["CPF_CNPJ_EMISSOR"])
        else:
            cnpj = None
        return f"CNPJ:{cnpj}" if cnpj else None

    def _emissor(self, arquivo: str, linha: dict[str, str]) -> str | None:
        """Empresa emissora pelo CNPJ. Só pessoa jurídica: o CPF nunca é lido."""
        if arquivo == "fi_BLC_5":
            cnpj = arquivos_cvm.cnpj(linha["CNPJ_EMISSOR"])
        elif "PF_PJ_EMISSOR" in linha and linha["PF_PJ_EMISSOR"].strip() == "PJ":
            cnpj = arquivos_cvm.cnpj(linha["CPF_CNPJ_EMISSOR"])
        else:
            cnpj = None
        return f"BR:CNPJ:{cnpj}" if cnpj else None

    def resultado(self) -> MesCDA:
        composicoes, nomes, confidencial, soma, patrimonio, valores = {}, {}, {}, {}, {}, {}
        sem_composicao = set()
        with localcontext(prec=PRECISAO):
            for cnpj, fundo in self.fundos.items():
                if not fundo.tem_linhas:
                    continue
                fundo_id = f"CNPJ:{cnpj}"
                pl = fundo.patrimonio
                if pl is None or fundo.data is None or pl <= 0:
                    sem_composicao.add(fundo_id)
                    motivo = "sem_patrimonio" if pl is None else "com_patrimonio_zero_ou_negativo"
                    self.descartes[f"fundo_{motivo}"] += 1
                    continue
                # Ordem estável (tipo e identificadores), para a carga comparar uma composição
                # com a publicada antes sem depender da ordem das linhas no arquivo.
                linhas = sorted(
                    ((chave, valor) for chave, valor in self.valores[cnpj].items() if valor != 0),
                    key=lambda par: tuple(parte or "" for parte in par[0]),
                )
                itens = tuple(
                    ItemComposicao(ativo_id, valor / pl, tipo, emissor=emissor, empresa_id=empresa)
                    for (tipo, ativo_id, empresa, emissor), valor in linhas
                )
                composicoes[fundo_id] = Composicao(fundo_id, fundo.data, FONTE, itens)
                valores[fundo_id] = tuple(valor for _, valor in linhas)
                patrimonio[fundo_id] = pl
                nomes[fundo_id] = fundo.nome
                soma[fundo_id] = fundo.soma / pl
                if fundo.confidencial:
                    confidencial[fundo_id] = fundo.confidencial / pl
        ambiguos = {t for t, isins in self.pares.items() if len(isins) > 1}
        self.descartes["ticker_com_dois_isins"] += len(ambiguos)
        listados = {t: c for t, c in self.fundos_listados.items() if len(c) == 1}
        self.descartes["ticker_de_fundo_com_dois_cnpjs"] += len(self.fundos_listados) - len(
            listados
        )
        return MesCDA(
            composicoes=composicoes,
            nomes=nomes,
            confidencial=confidencial,
            sem_composicao_utilizavel=frozenset(sem_composicao),
            soma_das_linhas=soma,
            isin_do_ticker={t: next(iter(i)) for t, i in self.pares.items() if t not in ambiguos},
            cnpj_do_fundo_listado={t: next(iter(c)) for t, c in listados.items()},
            descartes=+self.descartes,
            patrimonio=patrimonio,
            valores=valores,
        )
