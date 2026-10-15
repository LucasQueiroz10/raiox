"""Aviso tipo_corrigido (ADR 0005, seção 5): para um ativo que a base conhece, vale o tipo dela, e
a resposta avisa quando ele diverge do marcado, para a pessoa entender onde a posição foi parar.

O aviso aponta a posição pelo índice na lista enviada, como o 422 aponta o campo, e traz o tipo
usado: a resposta não repete o identificador nem o valor, e nada vai para o log.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.api.raiox import obter_repositorio
from app.dados.exemplo import RepositorioExemplo
from app.main import app

FII, ACAO = "ZZFL11", "ZZBC3"  # tickers do conjunto de exemplo: um FII e o Banco Exemplo
DESCONHECIDO = "ZZQQ3"  # ticker válido que a base não conhece


@pytest.fixture
def cliente():
    app.dependency_overrides[obter_repositorio] = RepositorioExemplo
    yield TestClient(app)
    app.dependency_overrides.clear()


def ticker(codigo: str, tipo: str, valor: str = "100.00") -> dict:
    return {
        "tipo_identificador": "ticker_b3",
        "identificador": codigo,
        "valor": valor,
        "moeda": "BRL",
        "tipo": tipo,
    }


def avisos(cliente: TestClient, *posicoes: dict) -> list[dict]:
    resposta = cliente.post("/api/raiox", json={"posicoes": list(posicoes)})
    assert resposta.status_code == 200
    return resposta.json()["avisos"]


def test_fii_marcado_como_acao_avisa_que_virou_fundo(cliente):
    assert avisos(cliente, ticker(FII, "acao")) == [
        {"codigo": "tipo_corrigido", "fundo_id": None, "posicao": 0, "tipo": "fundo"}
    ]


def test_acao_marcada_como_fundo_avisa_que_virou_acao(cliente):
    assert avisos(cliente, ticker(ACAO, "fundo")) == [
        {"codigo": "tipo_corrigido", "fundo_id": None, "posicao": 0, "tipo": "acao"}
    ]


def test_tipo_marcado_certo_nao_avisa(cliente):
    assert avisos(cliente, ticker(FII, "fundo"), ticker(ACAO, "acao")) == []


def test_identificador_desconhecido_nao_avisa_e_vale_o_marcado(cliente):
    resposta = cliente.post("/api/raiox", json={"posicoes": [ticker(DESCONHECIDO, "acao")]})
    corpo = resposta.json()

    assert corpo["avisos"] == []
    # Vale o marcado: a ação desconhecida entra como empresa sem classificação.
    assert [e["empresa_id"] for e in corpo["empresas"]] == [f"B3:{DESCONHECIDO}"]


def test_com_varias_posicoes_cada_aviso_aponta_o_indice_certo(cliente):
    posicoes = [
        ticker(ACAO, "acao"),
        ticker(FII, "acao"),  # 1: corrigido
        ticker(DESCONHECIDO, "fundo"),  # vale o marcado: fundo sem composição
        ticker(ACAO, "fundo"),  # 3: corrigido
    ]

    # Os avisos de posição vêm primeiro, na ordem da entrada; depois os da abertura dos fundos.
    assert avisos(cliente, *posicoes) == [
        {"codigo": "tipo_corrigido", "fundo_id": None, "posicao": 1, "tipo": "fundo"},
        {"codigo": "tipo_corrigido", "fundo_id": None, "posicao": 3, "tipo": "acao"},
        {
            "codigo": "fundo_sem_composicao",
            "fundo_id": f"B3:{DESCONHECIDO}",
            "posicao": None,
            "tipo": None,
        },
    ]


def test_o_aviso_nao_leva_nada_da_carteira_ao_log(cliente, caplog):
    with caplog.at_level(logging.DEBUG):
        avisos(cliente, ticker(FII, "acao", valor="4242.17"))

    for marcador in (FII, "4242.17", "tipo_corrigido"):
        assert marcador not in caplog.text
