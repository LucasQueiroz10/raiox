"""Respostas de erro que nunca repetem a entrada.

O 422 padrão do FastAPI devolve o valor enviado ("input") em cada erro, o que ecoaria a carteira.
Aqui ele informa só o campo, o motivo (código do Pydantic) e a mensagem.

Exceções não tratadas viram 500 genérico. A mensagem da exceção pode conter valores da carteira,
então ela não vai para a resposta nem para o log: o log registra só o tipo e onde ocorreu.
"""

import logging
from pathlib import Path
from traceback import extract_tb

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = logging.getLogger("rx.erros")


def _campo(erro: dict) -> list[str | int]:
    if erro["type"] == "json_invalid":
        return []  # a posição do caractere não ajuda e o campo não existe
    loc = list(erro["loc"])
    return loc[1:] if loc[:1] == ["body"] else loc


async def _entrada_invalida(_: Request, exc: RequestValidationError) -> JSONResponse:
    erros = [{"campo": _campo(e), "motivo": e["type"], "mensagem": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=422, content={"detail": {"codigo": "entrada_invalida", "erros": erros}}
    )


def _onde(exc: BaseException) -> str:
    quadros = extract_tb(exc.__traceback__)[-5:]
    return " <- ".join(f"{Path(q.filename).name}:{q.lineno} {q.name}" for q in reversed(quadros))


class ErroInternoGenerico:
    """Middleware ASGI: troca qualquer exceção não tratada por 500 genérico."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        iniciada = False

        async def enviar(mensagem: Message) -> None:
            nonlocal iniciada
            iniciada = iniciada or mensagem["type"] == "http.response.start"
            await send(mensagem)

        try:
            await self.app(scope, receive, enviar)
        except Exception as exc:
            log.error("erro interno %s em %s", type(exc).__name__, _onde(exc))
            if not iniciada:
                resposta = JSONResponse(
                    status_code=500, content={"detail": {"codigo": "erro_interno"}}
                )
                await resposta(scope, receive, send)


def registrar_erros(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _entrada_invalida)
    app.add_middleware(ErroInternoGenerico)
