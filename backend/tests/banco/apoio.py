"""Apoio aos testes com banco: conexão por usuário e aplicação das migrações.

O servidor de teste aceita conexão sem senha (como o do compose.yaml), então os usuários do projeto
entram só com o nome.
"""

from dataclasses import dataclass
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from banco.preparar import url_libpq

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def config_alembic() -> Config:
    return Config(str(ALEMBIC_INI))


@dataclass(frozen=True)
class BancoDeTeste:
    url_admin: str
    nome: str

    @property
    def admin(self) -> str:
        """Nome do usuário administrador do servidor de teste."""
        return make_url(self.url_admin).username or ""

    def url(self, usuario: str) -> str:
        """URL do SQLAlchemy para entrar no banco de teste como `usuario`."""
        url = make_url(self.url_admin).set(username=usuario, password=None, database=self.nome)
        return url.render_as_string(hide_password=False)

    def conectar(self, usuario: str) -> psycopg.Connection:
        return psycopg.connect(url_libpq(self.url(usuario)), autocommit=True)

    def conectar_admin(self) -> psycopg.Connection:
        url = make_url(self.url_admin).set(database=self.nome)
        return psycopg.connect(
            url_libpq(url.render_as_string(hide_password=False)), autocommit=True
        )

    def migrar(self, usuario: str) -> None:
        """Aplica as migrações como `usuario`, pelo mesmo caminho do `alembic upgrade head`."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("RX_BANCO_URL", self.url(usuario))
            command.upgrade(config_alembic(), "head")
