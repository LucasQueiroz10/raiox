"""Prepara um servidor PostgreSQL para o projeto (ADR 0006, seção 6): cria os usuários e o banco.

Roda uma vez por servidor, com um usuário administrador, antes das migrações. Tudo o que fica
dentro do banco (esquemas, tabelas, visões e permissões) vem das migrações, aplicadas pelo rx_dono.

Feito para o desenvolvimento e o CI, em que o servidor aceita conexão sem senha (compose.yaml): os
usuários são criados sem senha. Em produção, a autenticação fica fora do repositório e a preparação
segue o ADR de hospedagem.

Uso, dentro de backend/ (Git Bash), com o PostgreSQL do compose.yaml:
    export RX_BANCO_URL_ADMIN=postgresql+psycopg://postgres@127.0.0.1:5433/postgres
    python -m banco.preparar
"""

import os
import sys

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

DONO = "rx_dono"
# Usuários de antes do P3 (ADR 0006, seção 9). O rx_irrae e o grupo rx_admin_lista entram junto com
# as tabelas que eles usam.
PAPEIS = (DONO, "rx_api", "rx_ingestao")
BANCO = "rx"


def url_libpq(url: str) -> str:
    """Converte a URL do SQLAlchemy (postgresql+psycopg://...) na do psycopg (postgresql://...)."""
    return make_url(url).set(drivername="postgresql").render_as_string(hide_password=False)


def criar_papeis(conexao: psycopg.Connection) -> None:
    """Cria os usuários que faltam, sem poderes especiais. Os que já existem ficam como estão."""
    for papel in PAPEIS:
        existe = conexao.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (papel,)).fetchone()
        if existe is None:
            conexao.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION"
                    " NOBYPASSRLS"
                ).format(sql.Identifier(papel))
            )


def criar_banco(conexao: psycopg.Connection, nome: str) -> None:
    """Cria um banco vazio, do rx_dono. A conexão precisa estar em autocommit."""
    conexao.execute(
        sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE template0 ENCODING 'UTF8'").format(
            sql.Identifier(nome), sql.Identifier(DONO)
        )
    )


def main() -> None:
    url = os.environ.get("RX_BANCO_URL_ADMIN")
    if not url:
        sys.exit("Defina RX_BANCO_URL_ADMIN com o usuário administrador do servidor.")
    with psycopg.connect(url_libpq(url), autocommit=True) as conexao:
        criar_papeis(conexao)
        existe = conexao.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (BANCO,)
        ).fetchone()
        if existe is None:
            criar_banco(conexao, BANCO)
    print(f"Pronto: usuários {', '.join(PAPEIS)} e banco {BANCO}.")


if __name__ == "__main__":
    main()
