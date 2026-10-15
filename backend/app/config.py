"""Configuração lida das variáveis de ambiente do processo (nunca de arquivo .env).

RX_AMBIENTE: "desenvolvimento" (padrão) ou "producao". Em produção a documentação (/docs,
    /redoc, /openapi.json) é desligada e o HSTS é ligado.
RX_ORIGENS_PERMITIDAS: origens do front liberadas no CORS, separadas por vírgula. Sem ela,
    desenvolvimento libera só o Vite local e produção não libera nenhuma.
RX_BANCO_URL: conexão com o PostgreSQL (postgresql+psycopg://...), com o usuário rx_api
    (ADR 0006). Sem ela, a API usa o conjunto de exemplo sintético; em produção é obrigatória.
RX_SEGREDO_AQUECIMENTO: segredo que o Cloud Scheduler manda no aquecimento interno (ADR 0007,
    seção 3), com pelo menos 32 caracteres. Sem ele, o aquecimento não existe (responde 404).
RX_PROXIES_CONFIAVEIS: quantos proxies confiáveis acrescentam um endereço ao X-Forwarded-For,
    de 0 a 5; o IP do limite por IP é o N-ésimo endereço da direita (app/api/seguranca.py; DT-17).
    Sem ela, 0: o IP da conexão. Obrigatória em produção, porque no Cloud Run a conexão vem do
    Google e, com 0, todos os usuários dividiriam o mesmo limite.
"""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

AMBIENTES = ("desenvolvimento", "producao")
FRONT_LOCAL = "http://localhost:5173"
DRIVER_BANCO = "postgresql+psycopg://"
MIN_SEGREDO = 32
# Pedido direto ao Cloud Run: 1; pelo Firebase, provavelmente 2 (a confirmar no primeiro deploy).
MAX_PROXIES = 5


@dataclass(frozen=True)
class Config:
    producao: bool
    origens_permitidas: tuple[str, ...]
    # Em produção leva a senha: fica fora do repr, para não acabar em log.
    banco_url: str | None = field(default=None, repr=False)
    segredo_aquecimento: str | None = field(default=None, repr=False)
    proxies_confiaveis: int = 0

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
        # DT-17: sem a variável em produção, todos os usuários dividiriam o limite do IP do Google.
        bruto_proxies = ambiente.get("RX_PROXIES_CONFIAVEIS")
        if bruto_proxies is None:
            if producao:
                raise ValueError("RX_PROXIES_CONFIAVEIS é obrigatória em produção")
            proxies = 0
        else:
            # Só algarismos ASCII: str.isdigit aceitaria "²", e int() aceitaria "-1" e "+1".
            valor = bruto_proxies.strip()
            if re.fullmatch(r"[0-9]+", valor) is None or int(valor) > MAX_PROXIES:
                raise ValueError(f"RX_PROXIES_CONFIAVEIS deve ser um inteiro de 0 a {MAX_PROXIES}")
            proxies = int(valor)
        return cls(
            producao=producao,
            origens_permitidas=origens,
            banco_url=banco_url,
            segredo_aquecimento=segredo,
            proxies_confiaveis=proxies,
        )
