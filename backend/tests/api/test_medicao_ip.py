"""Medição do X-Forwarded-For no primeiro deploy (DT-17; ADR 0007, seção 3).

O Lucas chama uma vez pelo domínio e outra direto ao run.app, para ver em que posição o IP dele
chega e acertar RX_PROXIES_CONFIAVEIS. Como o aquecimento, fica fora do /api, exige o segredo no
cabeçalho e responde 404 sem ele. Devolve os endereços só para quem chamou, sem log.
"""

import logging

from fastapi.testclient import TestClient

from app.config import Config
from app.main import CABECALHO_AQUECIMENTO, criar_app

SEGREDO = "segredo-sintetico-de-teste-com-mais-de-32-caracteres"
CAMINHO = "/interno/ip-do-cliente"
XFF = ["203.0.113.9", "198.51.100.20, 192.0.2.30"]  # blocos reservados para documentação


def _cliente(segredo: str | None = SEGREDO, proxies: int = 2) -> TestClient:
    config = Config(
        producao=False,
        origens_permitidas=(),
        segredo_aquecimento=segredo,
        proxies_confiaveis=proxies,
    )
    return TestClient(criar_app(config))


def _pedir(cliente: TestClient, segredo: str | None = SEGREDO):
    cabecalhos = [("x-forwarded-for", v) for v in XFF]
    if segredo is not None:
        cabecalhos.append((CABECALHO_AQUECIMENTO, segredo))
    return cliente.get(CAMINHO, headers=cabecalhos)


def test_com_o_segredo_devolve_os_enderecos_na_ordem_e_a_chave_do_limite():
    r = _pedir(_cliente())

    assert r.status_code == 200
    assert r.json() == {
        "x_forwarded_for": ["203.0.113.9", "198.51.100.20", "192.0.2.30"],
        "proxies_confiaveis": 2,
        "chave_do_limite": "198.51.100.20",
    }
    assert r.headers["cache-control"] == "no-store"


def test_sem_o_cabecalho_ou_com_o_errado_responde_404():
    cliente = _cliente()

    sem = _pedir(cliente, segredo=None)
    errado = _pedir(cliente, segredo=SEGREDO + "x")

    assert sem.status_code == errado.status_code == 404
    assert sem.json() == errado.json() == cliente.get("/nao/existe").json()


def test_sem_segredo_configurado_a_medicao_nao_existe():
    assert _pedir(_cliente(segredo=None)).status_code == 404


def test_medicao_fica_fora_do_api_e_do_contrato():
    cliente = _cliente()

    r = cliente.get("/api" + CAMINHO, headers={CABECALHO_AQUECIMENTO: SEGREDO})

    assert r.status_code == 404
    assert not any("ip-do-cliente" in c for c in cliente.app.openapi()["paths"])


def test_nenhum_endereco_vai_para_o_log(caplog):
    caplog.set_level(logging.DEBUG)

    _pedir(_cliente())

    for endereco in ("203.0.113.9", "198.51.100.20", "192.0.2.30"):
        assert endereco not in caplog.text
