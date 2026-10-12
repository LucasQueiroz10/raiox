"""Testes com PostgreSQL (ADR 0006, seção 7).

Precisam de um servidor descartável, como o do compose.yaml, e da variável RX_BANCO_TESTE_URL com o
usuário administrador desse servidor (no compose: postgresql+psycopg://postgres@127.0.0.1:5433/postgres).
Sem a variável, os testes com banco são pulados; no CI (job "banco"), a falta dela é erro.
Cada banco de teste nasce vazio, recebe as migrações e é apagado no fim.
"""

import os
import secrets
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
import pytest
from psycopg import sql

from banco.preparar import criar_banco, criar_papeis, url_libpq
from tests.banco.apoio import BancoDeTeste


def _url_admin() -> str:
    url_admin = os.environ.get("RX_BANCO_TESTE_URL")
    if not url_admin:
        if os.environ.get("CI"):
            pytest.fail(
                "RX_BANCO_TESTE_URL não definida: no CI os testes com banco são obrigatórios."
            )
        pytest.skip(
            "Sem RX_BANCO_TESTE_URL: testes com banco pulados (ver tests/banco/conftest.py)."
        )
    return url_admin


@contextmanager
def _banco_de_teste(url_admin: str) -> Iterator[BancoDeTeste]:
    nome = f"rx_teste_{secrets.token_hex(4)}"
    with psycopg.connect(url_libpq(url_admin), autocommit=True) as admin:
        criar_papeis(admin)
        criar_banco(admin, nome)

    teste = BancoDeTeste(url_admin=url_admin, nome=nome)
    try:
        teste.migrar("rx_dono")
        yield teste
    finally:
        with psycopg.connect(url_libpq(url_admin), autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(nome))
            )


@pytest.fixture(scope="session")
def banco() -> Iterator[BancoDeTeste]:
    """Um banco para a rodada toda: cada teste usa os próprios identificadores."""
    with _banco_de_teste(_url_admin()) as teste:
        yield teste


@pytest.fixture
def banco_novo() -> Iterator[BancoDeTeste]:
    """Um banco só para o teste, para quem depende de qual foto foi publicada por último."""
    with _banco_de_teste(_url_admin()) as teste:
        yield teste
