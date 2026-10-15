"""Nada da carteira aparece nos logs, em nenhum caminho da requisição: sucesso ou qualquer erro.

Os valores e ISINs "marcadores" são sintéticos e só existem nesta carteira de teste.
"""

import logging
from datetime import date
from decimal import Decimal as D

from fastapi.testclient import TestClient

from app.api.raiox import obter_fonte_ptax, obter_limite_de_analises, obter_repositorio
from app.core.cambio import PtaxUsada
from app.core.identificadores import digito_verificador
from app.dados.exemplo import RepositorioExemplo
from app.main import app

_CORPO = "ZZMARCA0000"
ISIN_MARCADOR = _CORPO + digito_verificador(_CORPO)  # fora do conjunto de exemplo
MARCADORES = (ISIN_MARCADOR, "ZZCHIPS00019", "4242.17", "3131.29", "8080.91")

CARTEIRA = {
    "posicoes": [
        {
            "tipo_identificador": "isin",
            "identificador": ISIN_MARCADOR,
            "valor": "4242.17",
            "moeda": "BRL",
            "tipo": "acao",
        },
        {
            "tipo_identificador": "isin",
            "identificador": "ZZCHIPS00019",
            "valor": "3131.29",
            "moeda": "USD",
            "tipo": "acao",
        },
    ]
}
INVALIDA = {
    "posicoes": [
        {
            "tipo_identificador": "isin",
            "identificador": ISIN_MARCADOR,
            "valor": "-8080.91",
            "moeda": "BRL",
            "tipo": "x",
        }
    ]
}


class PtaxFixa:
    def cotacao(self, data_pedida=None):
        return PtaxUsada(date(2026, 9, 28), date(2026, 9, 25), D("5.0000"), date(2026, 9, 25))


class RepositorioQuebrado(RepositorioExemplo):
    def composicoes(self):
        raise RuntimeError(f"falha com {ISIN_MARCADOR} 4242.17")


def test_carteira_nunca_aparece_no_log(caplog):
    app.dependency_overrides[obter_repositorio] = RepositorioExemplo
    app.dependency_overrides[obter_fonte_ptax] = PtaxFixa
    cliente = TestClient(app)
    grande = b'{"posicoes": [' + ISIN_MARCADOR.encode() + b" " * (1024 * 1024) + b"]}"
    status = []

    try:
        with caplog.at_level(logging.DEBUG):
            status.append(cliente.post("/api/raiox", json=CARTEIRA).status_code)
            status.append(cliente.post("/api/raiox", json=INVALIDA).status_code)
            status.append(
                cliente.post(
                    "/api/raiox", content=grande, headers={"content-type": "application/json"}
                ).status_code
            )
            limite = obter_limite_de_analises()
            with limite.vaga(), limite.vaga(), limite.vaga(), limite.vaga():
                status.append(cliente.post("/api/raiox", json=CARTEIRA).status_code)
            app.dependency_overrides[obter_repositorio] = RepositorioQuebrado
            status.append(cliente.post("/api/raiox", json=CARTEIRA).status_code)
            while status[-1] != 429:
                status.append(cliente.post("/api/raiox", json=CARTEIRA).status_code)
    finally:
        app.dependency_overrides.clear()

    assert {200, 422, 413, 503, 500, 429} <= set(status)
    assert "RuntimeError" in caplog.text  # o log foi de fato capturado
    for marcador in MARCADORES:
        assert marcador not in caplog.text
