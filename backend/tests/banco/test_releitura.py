"""Releitura dos dados sem travar as análises (ADR 0007, seção 3; DT-10).

Um pedido só relê, fora da trava; os outros seguem com a foto anterior, sem esperar. A leitura da
foto é trocada por uma que só termina quando o teste libera, para provar isso sem depender de tempo.
"""

import threading
import time
from collections.abc import Iterator
from datetime import date

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from app.config import Config
from app.dados import postgres
from app.dados.postgres import (
    ESPERA_APOS_FALHA_S,
    INTERVALO_S,
    DadosIndisponiveis,
    RepositorioPostgres,
)
from app.main import criar_app
from tests.banco.apoio import (
    BancoDeTeste,
    abrir_carga,
    carregar_exemplo,
    inserir_composicao,
    publicar,
)
from tests.ficticios import isin

FUNDO_NOVO = "CNPJ:ZZ998877000008"


class Relogio:
    def __init__(self) -> None:
        self.agora = 0.0

    def __call__(self) -> float:
        return self.agora


class LeituraLenta:
    """Lê a foto de verdade, mas só depois que o teste libera; conta as leituras simultâneas."""

    def __init__(self, ler) -> None:
        self._ler = ler
        self._trava = threading.Lock()
        self.liberada = threading.Event()
        self.comecou = threading.Event()
        self.chamadas = 0
        self.ativas = 0
        self.maximo_simultaneas = 0

    def __call__(self, conexao):
        with self._trava:
            self.chamadas += 1
            self.ativas += 1
            self.maximo_simultaneas = max(self.maximo_simultaneas, self.ativas)
        self.comecou.set()
        try:
            assert self.liberada.wait(10), "a leitura não foi liberada"
            return self._ler(conexao)
        finally:
            with self._trava:
                self.ativas -= 1

    def zerar(self) -> None:
        self.liberada.clear()
        self.comecou.clear()
        self.chamadas = 0


@pytest.fixture
def relogio() -> Relogio:
    return Relogio()


@pytest.fixture
def repo(banco_novo: BancoDeTeste, relogio: Relogio) -> Iterator[RepositorioPostgres]:
    motor = create_engine(banco_novo.url("rx_api"))
    yield RepositorioPostgres(motor, relogio=relogio)
    motor.dispose()


@pytest.fixture
def ingestao(banco_novo: BancoDeTeste) -> Iterator[psycopg.Connection]:
    with banco_novo.conectar("rx_ingestao") as conexao:
        yield conexao


@pytest.fixture
def leitura(monkeypatch) -> Iterator[LeituraLenta]:
    lenta = LeituraLenta(postgres.ler_foto)
    monkeypatch.setattr(postgres, "ler_foto", lenta)
    yield lenta
    lenta.liberada.set()


def _publicar_fundo_novo(ingestao: psycopg.Connection) -> None:
    carga = abrir_carga(ingestao, "composicoes_cvm", date(2026, 9, 30))
    inserir_composicao(ingestao, carga, FUNDO_NOVO, date(2026, 9, 30), [(isin("N1"), "1", "acao")])
    publicar(ingestao, carga)


def _primeira_foto(repo: RepositorioPostgres, leitura: LeituraLenta):
    leitura.liberada.set()
    foto = repo.foto()
    leitura.zerar()
    return foto


def test_pedido_durante_releitura_lenta_usa_a_foto_anterior_sem_esperar(
    repo, ingestao, relogio, leitura
):
    carregar_exemplo(ingestao)
    anterior = _primeira_foto(repo, leitura)
    _publicar_fundo_novo(ingestao)
    relogio.agora += INTERVALO_S

    quem_rele = threading.Thread(target=repo.foto)
    quem_rele.start()
    assert leitura.comecou.wait(5)
    inicio = time.perf_counter()
    durante = repo.foto()
    espera = time.perf_counter() - inicio
    leitura.liberada.set()
    quem_rele.join(10)

    assert durante is anterior
    assert espera < 1  # não esperou a releitura, que só termina quando o teste libera
    assert FUNDO_NOVO in repo.foto().composicoes()


def test_duas_releituras_nunca_acontecem_ao_mesmo_tempo(repo, ingestao, relogio, leitura):
    carregar_exemplo(ingestao)
    _primeira_foto(repo, leitura)
    _publicar_fundo_novo(ingestao)
    relogio.agora += INTERVALO_S

    pedidos = [threading.Thread(target=repo.foto) for _ in range(6)]
    pedidos.append(threading.Thread(target=repo.aquecer))
    for p in pedidos:
        p.start()
    assert leitura.comecou.wait(5)
    time.sleep(0.3)  # tempo para os outros pedidos chegarem enquanto a releitura está parada
    leitura.liberada.set()
    for p in pedidos:
        p.join(10)

    assert leitura.maximo_simultaneas == 1
    assert leitura.chamadas == 1
    assert FUNDO_NOVO in repo.foto().composicoes()


def test_sem_foto_um_pedido_le_e_os_outros_recebem_503_na_hora(repo, ingestao, leitura):
    carregar_exemplo(ingestao)

    quem_le = threading.Thread(target=repo.foto)
    quem_le.start()
    assert leitura.comecou.wait(5)
    with pytest.raises(DadosIndisponiveis):
        repo.foto()
    leitura.liberada.set()
    quem_le.join(10)

    assert repo.foto().composicoes()


class MotorAlternavel:
    """Repassa ao motor de verdade até o teste derrubar o banco; conta as tentativas de conexão."""

    def __init__(self, motor) -> None:
        self._motor = motor
        self.fora_do_ar = False
        self.tentativas = 0

    def connect(self):
        self.tentativas += 1
        if self.fora_do_ar:
            raise OperationalError("SELECT 1", None, Exception("banco fora do ar (simulado)"))
        return self._motor.connect()

    def dispose(self) -> None:
        self._motor.dispose()


def test_releitura_que_falha_mantem_a_foto_e_espera_antes_de_tentar_de_novo(
    banco_novo, ingestao, relogio
):
    carregar_exemplo(ingestao)
    motor = MotorAlternavel(create_engine(banco_novo.url("rx_api")))
    repo = RepositorioPostgres(motor, relogio=relogio)
    anterior = repo.foto()
    motor.fora_do_ar = True
    antes = motor.tentativas

    relogio.agora += INTERVALO_S
    assert repo.foto() is anterior  # a releitura falhou: segue com a foto anterior
    relogio.agora += INTERVALO_S
    assert repo.foto() is anterior  # dentro da espera depois da falha: nem tenta
    assert motor.tentativas == antes + 1
    relogio.agora += ESPERA_APOS_FALHA_S
    repo.foto()
    assert motor.tentativas == antes + 2
    motor.dispose()


def test_aquecer_le_a_carga_nova_sem_esperar_o_intervalo(repo, ingestao):
    carregar_exemplo(ingestao)
    anterior = repo.foto()
    _publicar_fundo_novo(ingestao)

    assert repo.aquecer() is True
    assert repo.foto() is not anterior
    assert FUNDO_NOVO in repo.foto().composicoes()


def test_aquecer_sem_carga_nova_nao_rele(repo, ingestao, leitura):
    carregar_exemplo(ingestao)
    anterior = _primeira_foto(repo, leitura)
    leitura.liberada.set()

    assert repo.aquecer() is True
    assert leitura.chamadas == 0
    assert repo.foto() is anterior


def test_a_partida_do_servidor_le_os_dados_antes_do_primeiro_pedido(
    banco_novo, ingestao, monkeypatch
):
    carregar_exemplo(ingestao)
    leituras = []
    original = postgres.ler_foto
    monkeypatch.setattr(postgres, "ler_foto", lambda c: leituras.append(1) or original(c))
    config = Config(producao=False, origens_permitidas=(), banco_url=banco_novo.url("rx_api"))

    with TestClient(criar_app(config)) as cliente:
        na_partida = len(leituras)
        cliente.get("/api/saude")

    assert na_partida == 1
    assert len(leituras) == 1
