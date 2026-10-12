"""As rotas da API ficam sob /api em todos os ambientes (ADR 0007, seção 2): o Firebase Hosting
repassa o caminho inteiro, então /api/raiox chega à API como /api/raiox."""

from fastapi.testclient import TestClient

from app.config import Config
from app.main import criar_app

CARTEIRA = {
    "posicoes": [{"isin": "ZZBANCO00013", "valor": "500.00", "moeda": "BRL", "tipo": "acao"}]
}


def _cliente() -> TestClient:
    return TestClient(criar_app(Config(producao=False, origens_permitidas=())))


def test_rotas_respondem_sob_api():
    cliente = _cliente()

    assert cliente.get("/api/saude").status_code == 200
    assert cliente.post("/api/raiox", json=CARTEIRA).status_code == 200


def test_rotas_sem_o_prefixo_nao_existem():
    cliente = _cliente()

    assert cliente.get("/saude").status_code == 404
    assert cliente.post("/raiox", json=CARTEIRA).status_code == 404


def test_contrato_so_tem_rotas_sob_api():
    caminhos = criar_app(Config(producao=False, origens_permitidas=())).openapi()["paths"]

    assert caminhos
    assert all(c.startswith("/api/") for c in caminhos)
