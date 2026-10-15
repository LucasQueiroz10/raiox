"""De onde a API tira a PTAX do dia: do banco ou, sem banco, direto do Banco Central.

- **Com banco** (produção): `FontePtaxBanco` lê a `ref.ptax_vigente`, gravada pela carga diária
  (`cargas/ptax.py`). A API não chama o Banco Central (fechou a DT-1).
- **Sem banco** (desenvolvimento com o conjunto de exemplo): `FontePtax` busca na API PTAX do
  Banco Central, com cache em memória.

As duas escolhem a cotação pela mesma regra (`app/core/cambio.escolher_ptax`) e dizem o dia em que
ela foi obtida do Banco Central, para o aviso do BCB (`cambio.aviso_bcb` em docs/textos_telas.md).
"""

import json
import logging
import threading
import time
import urllib.request
from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal
from typing import Protocol

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.calendario import BRASILIA, hoje_em_brasilia
from app.core.cambio import PtaxUsada, escolher_ptax, ler_ptax_olinda

_BASE = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
JANELA_DIAS = 15  # dias pedidos ao BCB, para poder voltar se hoje ainda não tiver cotação
VALIDADE_CACHE_S = 3600  # a PTAX do dia sai por volta das 13h; 1 hora evita ficar com a de ontem
ESPERA_APOS_FALHA_S = 300  # BCB ou banco fora do ar: não faz cada análise esperar o timeout
TIMEOUT_S = 5
INTERVALO_S = 60  # com banco: de quanto em quanto tempo, no máximo, confere se saiu carga nova
# Com banco: cotações lidas, das mais recentes. A escolha volta no máximo 10 dias úteis.
COTACOES_LIDAS = 60

log = logging.getLogger(__name__)


class CambioIndisponivel(Exception):
    """Não há PTAX recente: nem no banco (ou no Banco Central, sem banco) nem guardada."""


class FonteCambio(Protocol):
    def cotacao(self, data_pedida: date | None = None) -> PtaxUsada:
        """A PTAX para a data pedida (hoje, em Brasília); levanta CambioIndisponivel sem cotação
        recente."""
        ...


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
    """Sem banco: busca no Banco Central na hora da análise, com cache de VALIDADE_CACHE_S."""

    def __init__(
        self,
        buscar: Callable[[date, date], dict] = buscar_olinda,
        hoje: Callable[[], date] = hoje_em_brasilia,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._buscar = buscar
        self._hoje = hoje
        self._relogio = relogio
        self._trava = threading.Lock()
        self._cotacoes: dict[date, Decimal] | None = None
        self._consultado_em: date | None = None  # dia da última busca que deu certo
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
            self._consultado_em = hoje
            self._proxima_busca = agora + VALIDADE_CACHE_S
        except (OSError, ValueError) as erro:
            self._proxima_busca = agora + ESPERA_APOS_FALHA_S
            if self._cotacoes is None:
                raise CambioIndisponivel("PTAX indisponível no Banco Central") from erro
            # BCB fora do ar: segue com a última cotação guardada.

    def cotacao(self, data_pedida: date | None = None) -> PtaxUsada:
        with self._trava:
            self._atualizar()
            cotacoes = self._cotacoes or {}
            consultas = dict.fromkeys(cotacoes, self._consultado_em)
            try:
                return escolher_ptax(cotacoes, data_pedida or self._hoje(), consultas)
            except LookupError as erro:
                raise CambioIndisponivel("sem PTAX recente") from erro


class FontePtaxBanco:
    """Com banco: a PTAX gravada pela carga diária (`cargas/ptax.py`), lida da `ref.ptax_vigente`.

    Guarda as cotações recentes em memória e só relê quando sai uma carga nova de PTAX, conferindo
    no máximo a cada INTERVALO_S. Fica fora da foto dos dados (`app/dados/postgres.py`) para uma
    PTAX nova, todo dia, não obrigar a reler as composições. Como a foto, a releitura não trava as
    análises: um pedido só relê, e os outros seguem com o que já está na memória. Com o banco fora
    do ar, segue com a última leitura e só tenta de novo depois de ESPERA_APOS_FALHA_S.
    """

    def __init__(
        self,
        motor: Engine,
        *,
        hoje: Callable[[], date] = hoje_em_brasilia,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._motor = motor
        self._hoje = hoje
        self._relogio = relogio
        # A trava protege só a marcação e a troca das cotações: ninguém espera nela pelo banco.
        self._trava = threading.Lock()
        self._relendo = False
        self._proxima_conferencia = 0.0
        self._versao: tuple | None = None
        # (valor por data de cotação, dia da consulta ao Banco Central por data de cotação)
        self._cotacoes: tuple[dict[date, Decimal], dict[date, date]] | None = None

    def cotacao(self, data_pedida: date | None = None) -> PtaxUsada:
        if self._tomar_a_vez():
            self._conferir()
        cotacoes = self._cotacoes
        if cotacoes is None:
            raise CambioIndisponivel("PTAX indisponível no banco")
        valores, consultas = cotacoes
        try:
            return escolher_ptax(valores, data_pedida or self._hoje(), consultas)
        except LookupError as erro:
            raise CambioIndisponivel("sem PTAX recente no banco") from erro

    def _tomar_a_vez(self) -> bool:
        with self._trava:
            if self._relendo or self._relogio() < self._proxima_conferencia:
                return False
            self._relendo = True
            return True

    def _conferir(self) -> None:
        espera = INTERVALO_S
        try:
            with self._motor.connect() as conexao:
                conexao.execution_options(
                    isolation_level="REPEATABLE READ", postgresql_readonly=True
                )
                versao = tuple(
                    conexao.execute(
                        text(
                            "SELECT count(*), max(publicada_em) FROM ref.carga_publicada"
                            " WHERE tipo = 'ptax'"
                        )
                    ).one()
                )
                if self._cotacoes is None or versao != self._versao:
                    linhas = conexao.execute(
                        text(
                            "SELECT v.data_cotacao, v.valor, c.publicada_em"
                            " FROM ref.ptax_vigente v JOIN ref.carga_publicada c USING (carga_id)"
                            " ORDER BY v.data_cotacao DESC LIMIT :n"
                        ),
                        {"n": COTACOES_LIDAS},
                    ).all()
                    valores = {r.data_cotacao: r.valor for r in linhas}
                    # O dia, em Brasília, em que a carga obteve a cotação do Banco Central.
                    consultas = {
                        r.data_cotacao: r.publicada_em.astimezone(BRASILIA).date() for r in linhas
                    }
                    with self._trava:
                        self._cotacoes, self._versao = (valores, consultas), versao
        except SQLAlchemyError as erro:
            espera = ESPERA_APOS_FALHA_S if self._cotacoes is not None else INTERVALO_S
            # Só o tipo do erro: a mensagem do driver pode trazer o endereço do banco.
            log.warning("Falha ao ler a PTAX do banco (%s).", type(erro).__name__)
        finally:
            with self._trava:
                self._proxima_conferencia = self._relogio() + espera
                self._relendo = False
