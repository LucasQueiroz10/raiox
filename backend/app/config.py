"""Configuração lida das variáveis de ambiente do processo (nunca de arquivo .env).

RX_AMBIENTE: "desenvolvimento" (padrão) ou "producao". Em produção a documentação (/docs,
    /redoc, /openapi.json) é desligada e o HSTS é ligado.
RX_ORIGENS_PERMITIDAS: origens do front liberadas no CORS, separadas por vírgula. Sem ela,
    desenvolvimento libera só o Vite local e produção não libera nenhuma.
RX_BANCO_URL: conexão com o PostgreSQL (postgresql+psycopg://...), com o usuário rx_api
    (ADR 0006). Sem ela, a API usa o conjunto de exemplo sintético; em produção é obrigatória.
RX_SEGREDO_AQUECIMENTO: segredo que o Cloud Scheduler manda no aquecimento interno (ADR 0007,
    seção 3), com pelo menos 32 caracteres. Sem ele, o aquecimento não existe (responde 404).
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

AMBIENTES = ("desenvolvimento", "producao")
FRONT_LOCAL = "http://localhost:5173"
DRIVER_BANCO = "postgresql+psycopg://"
MIN_SEGREDO = 32


@dataclass(frozen=True)
class Config:
    producao: bool
    origens_permitidas: tuple[str, ...]
    # Em produção leva a senha: fica fora do repr, para não acabar em log.
    banco_url: str | None = field(default=None, repr=False)
    segredo_aquecimento: str | None = field(default=None, repr=False)

    @classmethod
    def do_ambiente(cls, ambiente: Mapping[str, str] = os.environ) -> Config:
        nome = ambiente.get("RX_AMBIENTE", "desenvolvimento")
        if nome not in AMBIENTES:
            raise ValueError(f"RX_AMBIENTE deve ser um de {AMBIENTES}")
        producao = nome == "producao"

        bruto = ambiente.get("RX_ORIGENS_PERMITIDAS")
        if bruto is None:
            origens: tuple[str, ...] = () if producao else (FRONT_LOCAL,)
        else:
            origens = tuple(o.strip() for o in bruto.split(",") if o.strip())
        for origem in origens:
            if not origem.startswith(("https://", "http://")):
                raise ValueError(
                    "RX_ORIGENS_PERMITIDAS: cada origem precisa do esquema, ex.: https://rx.exemplo"
                )

        # As mensagens nunca repetem a URL, que pode levar a senha.
        banco_url = ambiente.get("RX_BANCO_URL") or None
        if banco_url is None and producao:
            raise ValueError("RX_BANCO_URL é obrigatória em produção")
        if banco_url is not None:
            if not banco_url.startswith(DRIVER_BANCO):
                raise ValueError(f"RX_BANCO_URL deve começar com {DRIVER_BANCO}")
            try:
                make_url(banco_url)
            except ValueError, ArgumentError:
                raise ValueError("RX_BANCO_URL malformada") from None

        segredo = ambiente.get("RX_SEGREDO_AQUECIMENTO") or None
        if segredo is not None and len(segredo) < MIN_SEGREDO:
            raise ValueError(
                f"RX_SEGREDO_AQUECIMENTO precisa de pelo menos {MIN_SEGREDO} caracteres"
            )
        return cls(
            producao=producao,
            origens_permitidas=origens,
            banco_url=banco_url,
            segredo_aquecimento=segredo,
        )
