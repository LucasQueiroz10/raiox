"""Respostas de erro nunca repetem o que a pessoa enviou: a carteira não volta no 422 nem no 500.

Os valores "marcadores" abaixo são sintéticos e fáceis de procurar no corpo da resposta e no log.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.api.raiox import obter_repositorio
from app.dados.exemplo import RepositorioExemplo
from app.main import app

FOF = "ZZFOF0000016"


@pytest.fixture
def cliente():
    app.dependency_overrides[obter_repositorio] = RepositorioExemplo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_422_informa_campo_e_motivo_sem_repetir_os_valores(cliente):
    entrada = {
        "posicoes": [
            {
                "isin": "USZQ4X7K2W18",  # dígito verificador errado
                "valor": "-987654.32",
                "moeda": "XQZ",
                "tipo": "acao",
                "apelido": "Fulano Sintetico",
            }
        ]
    }

    r = cliente.post("/raiox", json=entrada)

    assert r.status_code == 422
    detalhe = r.json()["detail"]
    assert detalhe["codigo"] == "entrada_invalida"
    erros = {tuple(e["campo"]): e["motivo"] for e in detalhe["erros"]}
    assert erros == {
        ("posicoes", 0, "isin"): "value_error",
        ("posicoes", 0, "valor"): "greater_than",
        ("posicoes", 0, "moeda"): "literal_error",
        ("posicoes", 0, "apelido"): "extra_forbidden",
    }
    assert all(set(e) == {"campo", "motivo", "mensagem"} for e in detalhe["erros"])
    for enviado in ("USZQ4X7K2W18", "987654", "XQZ", "Fulano"):
        assert enviado not in r.text


def test_limite_de_fundos_aponta_o_campo_sem_devolver_a_carteira(cliente):
    fundos = [{"isin": FOF, "valor": "1.00", "moeda": "BRL", "tipo": "fundo"}] * 101

    r = cliente.post("/raiox", json={"posicoes": fundos})

    assert r.status_code == 422
    assert [e["campo"] for e in r.json()["detail"]["erros"]] == [["posicoes"]]
    assert FOF not in r.text


def test_json_malformado_da_422_sem_repetir_o_corpo(cliente):
    r = cliente.post(
        "/raiox",
        content=b'{"posicoes": [MARCADOR_SINTETICO',
        headers={"content-type": "application/json"},
    )

    assert r.status_code == 422
    assert r.json()["detail"]["erros"][0] == {
        "campo": [],
        "motivo": "json_invalid",
        "mensagem": "JSON decode error",
    }
    assert "MARCADOR" not in r.text


class RepositorioQuebrado(RepositorioExemplo):
    def composicoes(self):
        raise RuntimeError("detalhe interno ZZBANCO00013 valor 123456.78")


def test_erro_inesperado_da_500_generico_e_o_log_so_tem_o_tipo(cliente, caplog):
    app.dependency_overrides[obter_repositorio] = RepositorioQuebrado
    carteira = {"posicoes": [{"isin": FOF, "valor": "1.00", "moeda": "BRL", "tipo": "fundo"}]}

    with caplog.at_level(logging.DEBUG):
        r = cliente.post("/raiox", json=carteira)

    assert r.status_code == 500
    assert r.json() == {"detail": {"codigo": "erro_interno"}}
    assert "RuntimeError" in caplog.text
    for vazamento in ("detalhe interno", "ZZBANCO00013", "123456.78", FOF):
        assert vazamento not in r.text
        assert vazamento not in caplog.text
