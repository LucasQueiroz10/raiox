"""Apoio aos testes com banco: conexão por usuário e aplicação das migrações.

O servidor de teste aceita conexão sem senha (como o do compose.yaml), então os usuários do projeto
entram só com o nome.
"""

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from app.dados.exemplo import RepositorioExemplo
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


# --- Cargas sintéticas (ADR 0006, seção 5), pelos mesmos comandos que a ingestão usa ---


def abrir_carga(conexao: psycopg.Connection, tipo: str, data_referencia: date | None = None) -> int:
    """Registra uma carga nova, que nasce "carregando", e devolve o carga_id."""
    linha = conexao.execute(
        "INSERT INTO ref.carga (tipo, fonte, data_referencia) VALUES (%s, %s, %s)"
        " RETURNING carga_id",
        (tipo, "fonte sintética", data_referencia),
    ).fetchone()
    return linha[0]


def publicar(conexao: psycopg.Connection, carga_id: int, linhas: int = 0) -> None:
    conexao.execute(
        "UPDATE ref.carga SET status = 'publicada', linhas = %s WHERE carga_id = %s",
        (linhas, carga_id),
    )


def inserir_composicao(
    conexao: psycopg.Connection,
    carga_id: int,
    fundo_id: str,
    data_referencia: date,
    itens: list[tuple[str | None, str, str]],
) -> int:
    """Grava uma composição com itens (ativo_id, peso, tipo) e devolve o composicao_id."""
    composicao_id = conexao.execute(
        "INSERT INTO ref.composicao (carga_id, fundo_id, nome_fundo, data_referencia, moeda)"
        " VALUES (%s, %s, %s, %s, 'BRL') RETURNING composicao_id",
        (carga_id, fundo_id, "Fundo Sintético", data_referencia),
    ).fetchone()[0]
    for ordem, (ativo_id, peso, tipo) in enumerate(itens, start=1):
        conexao.execute(
            "INSERT INTO ref.composicao_item (composicao_id, ordem, ativo_id, tipo, peso)"
            " VALUES (%s, %s, %s, %s, %s)",
            (composicao_id, ordem, ativo_id, tipo, Decimal(peso)),
        )
    return composicao_id


EXEMPLO = Path(__file__).resolve().parents[2] / "app" / "dados" / "exemplo.json"


def carregar_exemplo(conexao: psycopg.Connection) -> None:
    """Publica o conjunto de exemplo (app/dados/exemplo.json) em três cargas, como a ingestão
    faria: identificação, classificação e composições. A classificação e as composições saem do
    RepositorioExemplo, com o status de cada linha calculado pelo motor."""
    dados = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    exemplo = RepositorioExemplo()
    composicoes = exemplo.composicoes()

    carga = abrir_carga(conexao, "identificacao")
    for e in dados["empresas"]:
        conexao.execute(
            "INSERT INTO ref.empresa (carga_id, empresa_id, nome) VALUES (%s, %s, %s)",
            (carga, e["empresa_id"], e["nome"]),
        )
        for a in e["ativos"]:
            # Os ativos do exemplo são ISINs sintéticos: o ISIN é o próprio ativo_id.
            conexao.execute(
                "INSERT INTO ref.ativo"
                " (carga_id, ativo_id, tipo, empresa_id, nome, ticker_b3, isin)"
                " VALUES (%s, %s, 'acao', %s, %s, %s, %s)",
                (
                    carga,
                    a["ativo_id"],
                    e["empresa_id"],
                    a.get("nome"),
                    a.get("ticker_b3"),
                    a["ativo_id"],
                ),
            )
    for fundo in sorted(composicoes):
        conexao.execute(
            "INSERT INTO ref.ativo (carga_id, ativo_id, tipo, nome, ticker_b3, isin)"
            " VALUES (%s, %s, 'fundo', %s, %s, %s)",
            (
                carga,
                fundo,
                dados["nomes"][fundo],
                dados["tickers_b3_dos_fundos"].get(fundo),
                fundo,
            ),
        )
    publicar(conexao, carga)

    carga = abrir_carga(conexao, "classificacao")
    for c in exemplo.tabela_classificacao().classificacoes.values():
        conexao.execute(
            "INSERT INTO ref.classificacao"
            " (carga_id, empresa_id, setor, setor_origem, setor_status)"
            " VALUES (%s, %s, %s, %s, %s)",
            (carga, c.empresa_id, c.setor, c.setor_origem.value, c.setor_status.value),
        )
        for t in c.temas:
            conexao.execute(
                "INSERT INTO ref.classificacao_tema"
                " (carga_id, empresa_id, tema, subtema, peso, origem, status)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (carga, c.empresa_id, t.tema, t.subtema, t.peso, t.origem.value, t.status.value),
            )
    publicar(conexao, carga)

    (fonte,) = {c.fonte for c in composicoes.values()}
    carga = conexao.execute(
        "INSERT INTO ref.carga (tipo, fonte) VALUES ('composicoes_cvm', %s) RETURNING carga_id",
        (fonte,),
    ).fetchone()[0]
    for c in composicoes.values():
        composicao_id = conexao.execute(
            "INSERT INTO ref.composicao (carga_id, fundo_id, nome_fundo, data_referencia, moeda)"
            " VALUES (%s, %s, %s, %s, 'BRL') RETURNING composicao_id",
            (carga, c.fundo_id, dados["nomes"][c.fundo_id], c.data_referencia),
        ).fetchone()[0]
        for ordem, i in enumerate(c.itens, start=1):
            conexao.execute(
                "INSERT INTO ref.composicao_item (composicao_id, ordem, ativo_id, empresa_id,"
                " tipo, peso, ativo_objeto, emissor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    composicao_id,
                    ordem,
                    i.ativo_id,
                    i.empresa_id,
                    i.tipo.value,
                    i.peso,
                    i.ativo_objeto,
                    i.emissor,
                ),
            )
    publicar(conexao, carga)
