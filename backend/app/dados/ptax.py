"""Busca da PTAX na API do Banco Central, com cache em memória.

DT-1 (docs/divida_tecnica.md): o cache é por servidor. Com o banco, a ingestão diária
grava a PTAX e a API passa a só ler.
"""

import json
import threading
import time
import urllib.request
from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal

from app.core.cambio import PtaxUsada, escolher_ptax, ler_ptax_olinda

_BASE = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
JANELA_DIAS = 15  # dias pedidos ao BCB, para poder voltar se hoje ainda não tiver cotação
VALIDADE_CACHE_S = 3600  # a PTAX do dia sai por volta das 13h; 1 hora evita ficar com a de ontem
ESPERA_APOS_FALHA_S = 300  # com o BCB fora do ar, não faz cada análise esperar o timeout
TIMEOUT_S = 5


class CambioIndisponivel(Exception):
    """Não há PTAX disponível: o BCB não respondeu e não há cotação guardada."""


def montar_url(inicio: date, fim: date) -> str:
    return (
        f"{_BASE}CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
        f"?@dataInicial='{inicio:%m-%d-%Y}'&@dataFinalCotacao='{fim:%m-%d-%Y}'"
        "&$format=json&$select=cotacaoVenda,dataHoraCotacao"
    )


def buscar_olinda(inicio: date, fim: date) -> dict:
    """Chama a API PTAX do Banco Central. Endereço fixo e HTTPS; só datas saem do servidor."""
    pedido = urllib.request.Request(  # noqa: S310 - URL fixa em https://olinda.bcb.gov.br
        montar_url(inicio, fim), headers={"User-Agent": "ProjetoRX/0.1"}
    )
    with urllib.request.urlopen(pedido, timeout=TIMEOUT_S) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


class FontePtax:
    def __init__(
        self,
        buscar: Callable[[date, date], dict] = buscar_olinda,
        hoje: Callable[[], date] = date.today,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._buscar = buscar
        self._hoje = hoje
        self._relogio = relogio
        self._trava = threading.Lock()
        self._cotacoes: dict[date, Decimal] | None = None
        self._proxima_busca: float | None = None

    def _atualizar(self) -> None:
        agora = self._relogio()
        if self._proxima_busca is not None and agora < self._proxima_busca:
            if self._cotacoes is None:
                raise CambioIndisponivel("PTAX indisponível no Banco Central")
            return
        hoje = self._hoje()
        try:
            self._cotacoes = ler_ptax_olinda(self._buscar(hoje - timedelta(days=JANELA_DIAS), hoje))
            self._proxima_busca = agora + VALIDADE_CACHE_S
        except (OSError, ValueError) as erro:
            self._proxima_busca = agora + ESPERA_APOS_FALHA_S
            if self._cotacoes is None:
                raise CambioIndisponivel("PTAX indisponível no Banco Central") from erro
            # BCB fora do ar: segue com a última cotação guardada.

    def cotacao(self, data_pedida: date | None = None) -> PtaxUsada:
        with self._trava:
            self._atualizar()
            try:
                return escolher_ptax(self._cotacoes or {}, data_pedida or self._hoje())
            except LookupError as erro:
                raise CambioIndisponivel("sem PTAX recente") from erro
