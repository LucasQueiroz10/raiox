from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine

from app.api import raiox, saude
from app.api.erros import ErroInternoGenerico, entrada_invalida
from app.api.seguranca import CabecalhosDeSeguranca, LimiteDeCorpo
from app.config import Config
from app.dados.exemplo import RepositorioExemplo
from app.dados.postgres import RepositorioPostgres
from app.dados.repositorio import FonteDados

MAX_CORPO = 1024 * 1024  # 1 MB; 500 posições ocupam uns 50 KB
ESPERA_CONEXAO_S = 5  # com o banco fora do ar, a análise responde 503 logo, sem ficar presa


def _fonte_dos_dados(config: Config) -> FonteDados:
    """Banco quando RX_BANCO_URL está definida; senão, o exemplo sintético (ADR 0006).
    Não conecta aqui: a primeira análise lê os dados."""
    if config.banco_url is None:
        return RepositorioExemplo()
    motor = create_engine(
        config.banco_url, pool_pre_ping=True, connect_args={"connect_timeout": ESPERA_CONEXAO_S}
    )
    return RepositorioPostgres(motor)


@asynccontextmanager
async def _ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    yield
    if isinstance(app.state.dados, RepositorioPostgres):
        app.state.dados.fechar()


def criar_app(config: Config) -> FastAPI:
    documentacao = not config.producao
    app = FastAPI(
        title="Projeto RX",
        docs_url="/docs" if documentacao else None,
        redoc_url="/redoc" if documentacao else None,
        openapi_url="/openapi.json" if documentacao else None,
        lifespan=_ciclo_de_vida,
    )
    app.state.dados = _fonte_dos_dados(config)
    app.add_exception_handler(RequestValidationError, entrada_invalida)

    # O último middleware adicionado é o mais externo. De fora para dentro:
    # cabeçalhos de segurança -> CORS -> 500 genérico -> limite de corpo -> rotas.
    app.add_middleware(LimiteDeCorpo, maximo=MAX_CORPO)
    app.add_middleware(ErroInternoGenerico)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.origens_permitidas),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        max_age=600,
    )
    app.add_middleware(CabecalhosDeSeguranca, hsts=config.producao, documentacao=documentacao)

    app.include_router(saude.router)
    app.include_router(raiox.router)
    return app


app = criar_app(Config.do_ambiente())
