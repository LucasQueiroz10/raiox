from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import raiox, saude
from app.api.erros import ErroInternoGenerico, entrada_invalida
from app.api.seguranca import CabecalhosDeSeguranca, LimiteDeCorpo
from app.config import Config

MAX_CORPO = 1024 * 1024  # 1 MB; 500 posições ocupam uns 50 KB


def criar_app(config: Config) -> FastAPI:
    documentacao = not config.producao
    app = FastAPI(
        title="Projeto RX",
        docs_url="/docs" if documentacao else None,
        redoc_url="/redoc" if documentacao else None,
        openapi_url="/openapi.json" if documentacao else None,
    )
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
