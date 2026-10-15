"""A API lê a PTAX do banco (ref.ptax_vigente), gravada pela carga diária (cargas/ptax.py; fecha a
DT-1). Cada teste usa um banco novo; o Banco Central da carga é simulado."""

from datetime import date
from decimal import Decimal as D

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from app.core.calendario import BRASILIA
from app.dados.ptax import ESPERA_APOS_FALHA_S, INTERVALO_S, CambioIndisponivel, FontePtaxBanco
from cargas.ptax import carregar

TER, QUA, SAB = date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 17)


class Relogio:
    def __init__(self) -> None:
        self.agora = 1000.0

    def __call__(self) -> float:
        return self.agora


class MotorAlternavel:
    """Motor que pode fingir que o banco caiu (como em test_releitura.py)."""

    def __init__(self, motor) -> None:
        self._motor = motor
        self.fora_do_ar = False

    def connect(self):
        if self.fora_do_ar:
            raise OperationalError("SELECT 1", None, Exception("banco fora do ar (simulado)"))
        return self._motor.connect()


@pytest.fixture
def motor(banco_novo):
    m = create_engine(banco_novo.url("rx_api"))
    yield m
    m.dispose()


def publicar(banco_novo, cotacoes: dict[date, D]) -> None:
    with banco_novo.conectar("rx_ingestao") as ingestao:
        carregar(ingestao, max(cotacoes), lambda inicio, fim: cotacoes)


def test_le_a_ptax_do_ultimo_dia_util_com_a_data_de_consulta(banco_novo, motor):
    publicar(banco_novo, {TER: D("5.2000"), QUA: D("5.3000")})
    with banco_novo.conectar("rx_api") as api:
        (publicada_em,) = api.execute(
            "SELECT publicada_em FROM ref.carga_publicada WHERE tipo = 'ptax'"
        ).fetchone()

    p = FontePtaxBanco(motor, hoje=lambda: SAB).cotacao()

    assert (p.data_pedida, p.data_cotacao, p.valor) == (SAB, QUA, D("5.3000"))
    # A data de consulta é o dia, em Brasília, em que a carga obteve a cotação do Banco Central.
    assert p.data_consulta == publicada_em.astimezone(BRASILIA).date()


def test_sem_ptax_no_banco_o_cambio_fica_indisponivel(motor):
    with pytest.raises(CambioIndisponivel):
        FontePtaxBanco(motor, hoje=lambda: QUA).cotacao()


def test_ptax_mais_antiga_que_10_dias_uteis_tambem_fica_indisponivel(banco_novo, motor):
    publicar(banco_novo, {date(2026, 9, 1): D("5.0000")})

    with pytest.raises(CambioIndisponivel):
        FontePtaxBanco(motor, hoje=lambda: QUA).cotacao()


def test_rele_quando_sai_carga_nova_de_ptax_no_maximo_a_cada_intervalo(banco_novo, motor):
    relogio = Relogio()
    publicar(banco_novo, {TER: D("5.2000")})
    fonte = FontePtaxBanco(motor, hoje=lambda: QUA, relogio=relogio)
    assert fonte.cotacao().data_cotacao == TER

    publicar(banco_novo, {TER: D("5.2000"), QUA: D("5.3000")})
    assert fonte.cotacao().data_cotacao == TER  # dentro do intervalo: nem confere
    relogio.agora += INTERVALO_S
    assert fonte.cotacao().data_cotacao == QUA


def test_banco_fora_do_ar_segue_com_a_ultima_leitura(banco_novo, motor):
    relogio = Relogio()
    publicar(banco_novo, {QUA: D("5.3000")})
    alternavel = MotorAlternavel(motor)
    fonte = FontePtaxBanco(alternavel, hoje=lambda: QUA, relogio=relogio)
    antes = fonte.cotacao()

    alternavel.fora_do_ar = True
    relogio.agora += INTERVALO_S

    assert fonte.cotacao() == antes
    relogio.agora += ESPERA_APOS_FALHA_S
    assert fonte.cotacao() == antes
