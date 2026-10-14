"""Medição do pico de memória das cargas: só roda contra um banco no próprio computador, porque
publica cargas de verdade (revisão do PR #70)."""

import pytest

from medicoes import pico_da_carga
from medicoes.pico_da_carga import banco_local, main

LOCAL = "postgresql+psycopg://rx_ingestao@127.0.0.1:5433/rx"
REMOTO = "postgresql+psycopg://rx_ingestao@banco.exemplo.invalid:5432/rx"


@pytest.mark.parametrize(
    "url", [LOCAL, "postgresql+psycopg://rx_ingestao@localhost/rx", "postgresql://u@LOCALHOST/rx"]
)
def test_aceita_banco_no_proprio_computador(url):
    assert banco_local(url)


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        REMOTO,
        "postgresql+psycopg://rx_ingestao@10.0.0.5:5432/rx",
        "postgresql+psycopg://rx_ingestao@localhost.exemplo.invalid/rx",
        # Sem host, o libpq usaria o PGHOST ou o socket: não dá para saber aonde vai.
        "postgresql+psycopg://rx_ingestao@/rx",
        # host e hostaddr na consulta passam por cima do host da URL no libpq.
        "postgresql+psycopg://rx_ingestao@localhost/rx?host=banco.exemplo.invalid",
        "postgresql+psycopg://rx_ingestao@127.0.0.1/rx?hostaddr=10.0.0.5",
        "não é uma url",
    ],
)
def test_recusa_qualquer_outro_banco(url):
    assert not banco_local(url)


@pytest.fixture
def chamadas(monkeypatch) -> list[list[str]]:
    """Troca a carga por uma falsa, que só anota os argumentos."""
    feitas: list[list[str]] = []
    monkeypatch.setitem(pico_da_carga.CARGAS, "cadastro", lambda argv: feitas.append(argv) or 0)
    return feitas


def test_recusa_rodar_fora_do_banco_local_sem_chamar_a_carga(monkeypatch, capsys, chamadas):
    monkeypatch.setenv("RX_BANCO_URL", REMOTO)

    assert main(["cadastro"]) == 2

    assert chamadas == []
    assert "banco.exemplo.invalid" not in capsys.readouterr().err  # nunca o endereço


def test_com_o_banco_local_roda_a_carga_e_imprime_o_pico(monkeypatch, capsys, chamadas):
    monkeypatch.setenv("RX_BANCO_URL", LOCAL)

    assert main(["cadastro", "--pasta", "zips"]) == 0

    assert chamadas == [["--pasta", "zips"]]
    assert "pico de memória do processo" in capsys.readouterr().out


def test_carga_desconhecida_e_erro_de_uso(monkeypatch):
    monkeypatch.setenv("RX_BANCO_URL", LOCAL)

    assert main(["ptax"]) == 2
