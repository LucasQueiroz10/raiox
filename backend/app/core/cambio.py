"""Câmbio pela PTAX do Banco Central: leitura da resposta, escolha da data e conversão.

Funções puras: a busca na API (rede) fica na ingestão.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

_FECHAMENTO = "Fechamento"


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
