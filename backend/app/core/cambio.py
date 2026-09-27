"""Câmbio pela PTAX do Banco Central: leitura da resposta, escolha da data e conversão.

Funções puras: a busca na API (rede) fica na ingestão.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from app.core.calendario import ultimo_dia_util

_FECHAMENTO = "Fechamento"
# Quantos dias úteis voltar quando o BCB não tem cotação na data calculada.
MAX_DIAS_UTEIS_SEM_COTACAO = 10


@dataclass(frozen=True, slots=True)
class PtaxUsada:
    """A cotação usada e as duas datas, para a tela mostrar de qual dia é a PTAX."""

    data_pedida: date
    data_cotacao: date
    valor: Decimal


def _decimal(valor: object) -> Decimal:
    """Converte pelo texto: Decimal(str(5.1234)) é exatamente 5.1234, sem erro de float."""
    try:
        d = Decimal(str(valor))
    except InvalidOperation as erro:
        raise ValueError("cotação não numérica") from erro
    if not d.is_finite() or d <= 0:
        raise ValueError("cotação precisa ser um número positivo")
    return d


def ler_ptax_olinda(resposta: dict) -> dict[date, Decimal]:
    """Resposta da API PTAX (Olinda) -> {data: cotação de venda}.

    Quando a resposta traz vários boletins no dia (abertura, intermediários e
    fechamento), usa só o de fechamento, que é a PTAX oficial.
    """
    linhas = resposta.get("value", [])
    if any("tipoBoletim" in linha for linha in linhas):
        linhas = [linha for linha in linhas if linha.get("tipoBoletim") == _FECHAMENTO]
    cotacoes = {}
    for linha in linhas:
        if "cotacaoVenda" not in linha:
            raise ValueError("linha da PTAX sem cotação de venda")
        dia = date.fromisoformat(str(linha["dataHoraCotacao"])[:10])
        cotacoes[dia] = _decimal(linha["cotacaoVenda"])
    return cotacoes


def escolher_ptax(cotacoes: Mapping[date, Decimal], data_pedida: date) -> PtaxUsada:
    """PTAX do último dia útil até a data pedida; se o BCB não tiver cotação nesse dia,
    volta dia útil a dia útil, até MAX_DIAS_UTEIS_SEM_COTACAO."""
    dia = ultimo_dia_util(data_pedida)
    for _ in range(MAX_DIAS_UTEIS_SEM_COTACAO):
        if dia in cotacoes:
            return PtaxUsada(data_pedida, dia, cotacoes[dia])
        dia = ultimo_dia_util(dia - timedelta(days=1))
    raise LookupError(f"sem PTAX nos {MAX_DIAS_UTEIS_SEM_COTACAO} dias úteis até {data_pedida}")
