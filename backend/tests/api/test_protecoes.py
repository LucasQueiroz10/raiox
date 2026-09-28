"""Proteções do servidor: limite por IP, análises simultâneas, tamanho do corpo, cabeçalhos,
CORS e documentação desligada em produção."""

import json

import pytest
from fastapi.testclient import TestClient

from app.api.raiox import obter_limite_de_analises, obter_repositorio
from app.config import Config
from app.dados.exemplo import RepositorioExemplo
from app.main import app, criar_app

CARTEIRA = {"posicoes": [{"isin": "ZZBANCO00013", "valor": "1.00", "moeda": "BRL", "tipo": "acao"}]}
UM_MB = 1024 * 1024
ORIGEM = "https://rx.exemplo"
JSON = {"content-type": "application/json"}


@pytest.fixture
def cliente():
    app.dependency_overrides[obter_repositorio] = RepositorioExemplo
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---- limite por IP -------------------------------------------------------------------------


def test_21a_analise_no_mesmo_minuto_da_429_com_retry_after(cliente):
    respostas = [cliente.post("/raiox", json=CARTEIRA) for _ in range(21)]

    assert [r.status_code for r in respostas[:20]] == [200] * 20
    ultima = respostas[20]
    assert ultima.status_code == 429
    assert ultima.json() == {"detail": {"codigo": "muitas_analises"}}
    assert 1 <= int(ultima.headers["retry-after"]) <= 60


def test_trocar_o_x_forwarded_for_nao_burla_o_limite(cliente):
    for i in range(20):
        cliente.post("/raiox", json=CARTEIRA, headers={"x-forwarded-for": f"203.0.113.{i}"})

    r = cliente.post("/raiox", json=CARTEIRA, headers={"x-forwarded-for": "198.51.100.7"})

    assert r.status_code == 429


def test_entrada_invalida_tambem_conta_no_limite(cliente):
    for _ in range(20):
        cliente.post("/raiox", json={"posicoes": []})

    assert cliente.post("/raiox", json=CARTEIRA).status_code == 429


def test_limite_de_analises_nao_bloqueia_a_saude(cliente):
    for _ in range(21):
        cliente.post("/raiox", json=CARTEIRA)

    assert cliente.get("/saude").status_code == 200


# ---- análises simultâneas ------------------------------------------------------------------


def test_com_4_analises_em_andamento_a_quinta_recebe_503(cliente):
    limite = obter_limite_de_analises()

    with limite.vaga(), limite.vaga(), limite.vaga():
        assert cliente.post("/raiox", json=CARTEIRA).status_code == 200
        with limite.vaga():
            r = cliente.post("/raiox", json=CARTEIRA)

    assert r.status_code == 503
    assert r.json() == {"detail": {"codigo": "servidor_ocupado"}}
    assert "retry-after" in r.headers
    assert cliente.post("/raiox", json=CARTEIRA).status_code == 200


# ---- tamanho do corpo ----------------------------------------------------------------------


def _com_tamanho(corpo: dict, tamanho: int) -> bytes:
    texto = json.dumps(corpo).encode("utf-8")
    return texto[:-1] + b" " * (tamanho - len(texto)) + texto[-1:]


def test_corpo_de_ate_1_mb_passa(cliente):
    corpo = _com_tamanho(CARTEIRA, UM_MB)

    assert len(corpo) == UM_MB
    assert cliente.post("/raiox", content=corpo, headers=JSON).status_code == 200


def test_corpo_acima_de_1_mb_da_413(cliente):
    r = cliente.post("/raiox", content=_com_tamanho(CARTEIRA, UM_MB + 1), headers=JSON)

    assert r.status_code == 413
    assert r.json() == {"detail": {"codigo": "corpo_grande_demais"}}


def test_corpo_em_partes_sem_content_length_tambem_e_limitado(cliente):
    def partes():
        yield b'{"posicoes": ['
        for _ in range(17):
            yield b" " * 65536
        yield b"]}"

    r = cliente.post("/raiox", content=partes(), headers=JSON)

    assert r.status_code == 413


# ---- cabeçalhos, CORS e documentação ------------------------------------------------------


def test_cabecalhos_de_seguranca_em_toda_resposta(cliente):
    respostas = [
        cliente.get("/saude"),
        cliente.post("/raiox", json=CARTEIRA),
        cliente.post("/raiox", json={}),
        cliente.post("/raiox", content=_com_tamanho(CARTEIRA, UM_MB + 1), headers=JSON),
        cliente.get("/nao-existe"),
    ]

    for r in respostas:
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["referrer-policy"] == "no-referrer"
        assert r.headers["x-frame-options"] == "DENY"
        assert r.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
        assert r.headers["cache-control"] == "no-store"
        assert "strict-transport-security" not in r.headers  # só em produção, atrás de HTTPS


def test_producao_tem_hsts_e_nao_expoe_a_documentacao():
    c = TestClient(criar_app(Config(producao=True, origens_permitidas=())))

    r = c.get("/saude")

    assert r.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"
    for caminho in ("/docs", "/redoc", "/openapi.json"):
        assert c.get(caminho).status_code == 404


def test_desenvolvimento_expoe_a_documentacao():
    c = TestClient(criar_app(Config(producao=False, origens_permitidas=())))

    assert c.get("/openapi.json").status_code == 200
    assert c.get("/docs").status_code == 200


def test_cors_libera_so_a_origem_do_front():
    c = TestClient(criar_app(Config(producao=True, origens_permitidas=(ORIGEM,))))
    pedido = {
        "access-control-request-method": "POST",
        "access-control-request-headers": "content-type",
    }

    do_front = c.options("/raiox", headers={"origin": ORIGEM, **pedido})
    de_fora = c.options("/raiox", headers={"origin": "https://outro.exemplo", **pedido})
    simples_de_fora = c.get("/saude", headers={"origin": "https://outro.exemplo"})

    assert do_front.status_code == 200
    assert do_front.headers["access-control-allow-origin"] == ORIGEM
    assert "access-control-allow-origin" not in de_fora.headers
    assert "access-control-allow-origin" not in simples_de_fora.headers
