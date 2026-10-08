"""Ambiente das migrações (ADR 0006, seção 8).

A conexão vem da variável RX_BANCO_URL e tem de ser do rx_dono, o dono dos esquemas: uma migração
aplicada por outro usuário criaria objetos com o dono errado. Não há modo sem conexão (--sql).
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, create_engine, pool, text

from banco.preparar import DONO

config = context.config


def _url() -> str:
    url = os.environ.get("RX_BANCO_URL")
    if not url:
        raise RuntimeError(f"Defina RX_BANCO_URL com o usuário {DONO} (ver backend/CLAUDE.md).")
    return url


def _migrar(conexao: Connection) -> None:
    usuario = conexao.execute(text("SELECT current_user")).scalar_one()
    if usuario != DONO:
        raise RuntimeError(f"As migrações rodam só como {DONO}; a conexão entrou como {usuario}.")

    # A tabela de versão do Alembic fica no esquema app, porque o public fica sem uso (ADR 0006,
    # seção 2). O Alembic cria essa tabela antes da primeira migração, então o esquema vem antes.
    conexao.execute(text("CREATE SCHEMA IF NOT EXISTS app"))
    conexao.commit()

    context.configure(connection=conexao, version_table_schema="app")
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Migrações sem conexão (--sql) não são usadas neste projeto.")

# Pela linha de comando, mostra o andamento. Chamado de dentro do Python (testes), não mexe no log
# de quem chamou.
if config.cmd_opts is not None and config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

motor = create_engine(_url(), poolclass=pool.NullPool)
try:
    with motor.connect() as conexao:
        _migrar(conexao)
finally:
    motor.dispose()
