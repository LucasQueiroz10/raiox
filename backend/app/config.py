"""Configuração lida das variáveis de ambiente do processo (nunca de arquivo .env).

RX_AMBIENTE: "desenvolvimento" (padrão) ou "producao". Em produção a documentação (/docs,
    /redoc, /openapi.json) é desligada e o HSTS é ligado.
RX_ORIGENS_PERMITIDAS: origens do front liberadas no CORS, separadas por vírgula. Sem ela,
    desenvolvimento libera só o Vite local e produção não libera nenhuma.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass

AMBIENTES = ("desenvolvimento", "producao")
FRONT_LOCAL = "http://localhost:5173"


@dataclass(frozen=True)
class Config:
    producao: bool
    origens_permitidas: tuple[str, ...]

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
        return cls(producao=producao, origens_permitidas=origens)
