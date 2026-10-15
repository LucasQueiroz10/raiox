from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from starlette.concurrency import run_in_threadpool

from app.api import interno, raiox, saude
from app.api.erros import ErroInternoGenerico, entrada_invalida
from app.api.interno import CABECALHO_AQUECIMENTO
from app.api.seguranca import CabecalhosDeSeguranca, LimiteDeCorpo
from app.config import Config
from app.dados.exemplo import RepositorioExemplo
from app.dados.postgres import RepositorioPostgres
from app.dados.ptax import FonteCambio, FontePtax, FontePtaxBanco
from app.dados.repositorio import FonteDados

MAX_CORPO = 1024 * 1024  # 1 MB; 500 posições ocupam uns 50 KB
# O Firebase Hosting repassa o caminho inteiro (/api/raiox chega como /api/raiox): as rotas ficam
# sob /api em todos os ambientes (ADR 0007, seção 2).
PREFIXO_API = "/api"
ESPERA_CONEXAO_S = 5  # com o banco fora do ar, a análise responde 503 logo, sem ficar presa


def _fontes(config: Config) -> tuple[FonteDados, FonteCambio]:
    """Os dados públicos e a PTAX. Com RX_BANCO_URL, os dois vêm do banco, pelo mesmo motor (ADR
    0006; a PTAX é gravada pela carga diária e a API não chama o Banco Central: DT-1 fechada).
    Sem ela, o exemplo sintético e a PTAX buscada no Banco Central (desenvolvimento). Não conecta
    aqui: a primeira leitura acontece na partida do servidor."""
    if config.banco_url is None:
        return RepositorioExemplo(), FontePtax()
    motor = create_engine(
        config.banco_url, pool_pre_ping=True, connect_args={"connect_timeout": ESPERA_CONEXAO_S}
    )
    return RepositorioPostgres(motor), FontePtaxBanco(motor)


@asynccontextmanager
async def _ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    # Primeira leitura dos dados antes de aceitar pedidos (ADR 0007, seção 3). Se o banco não
    # responder, o servidor sobe mesmo assim e as análises recebem 503 até uma leitura dar certo.
    await run_in_threadpool(app.state.dados.aquecer)
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
    app.state.dados, app.state.ptax = _fontes(config)
    app.state.segredo_aquecimento = config.segredo_aquecimento
    app.state.proxies_confiaveis = config.proxies_confiaveis
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

    app.include_router(saude.router, prefix=PREFIXO_API)
    app.include_router(raiox.router, prefix=PREFIXO_API)
    # Fora do /api: o Firebase não encaminha o aquecimento interno.
    app.include_router(interno.router)
    return app


__all__ = ["CABECALHO_AQUECIMENTO", "PREFIXO_API", "app", "criar_app"]

app = criar_app(Config.do_ambiente())
