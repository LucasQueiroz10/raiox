"""Proteções do servidor contra abuso: limite por IP, análises simultâneas, tamanho do corpo e
cabeçalhos de segurança.

DT-2: os contadores ficam na memória de cada servidor. Com N instâncias, o limite efetivo por IP
vira N vezes o configurado, e reiniciar o servidor zera a conta.

O IP do limite vem de chave_do_limite (DT-17): com RX_PROXIES_CONFIAVEIS=0, o IP da conexão; com
N, o N-ésimo endereço da direita do X-Forwarded-For. Quem lê o cabeçalho é a aplicação: o uvicorn
roda com --no-proxy-headers (Dockerfile). Nunca use --forwarded-allow-ips="*" sem um proxy que
sobrescreva esse cabeçalho: qualquer cliente escolheria o próprio IP.
"""

import ipaddress
import math
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager

from fastapi import HTTPException
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def chave_do_limite(
    cabecalhos_xff: Sequence[str], ip_conexao: str | None, proxies_confiaveis: int
) -> str:
    """A chave do limite por IP de um pedido (DT-17; ADR 0007, seção 3).

    No Cloud Run a conexão chega da infraestrutura do Google, e o IP do cliente vem no
    X-Forwarded-For. Cada proxy confiável acrescenta à direita o endereço de quem se conectou a
    ele; o que fica à esquerda pode ter sido escrito pelo próprio cliente. Por isso a chave é o
    N-ésimo endereço da direita (N = `proxies_confiaveis`), nunca o primeiro. Os vários cabeçalhos
    X-Forwarded-For contam como um só, na ordem em que chegaram.

    Com N = 0, com menos de N endereços (o pedido não veio pelo caminho esperado) ou com um valor
    que não é IP na posição, vale o IP da conexão. O IPv6 conta pela rede /64: quem tem uma
    rede inteira não zera o limite trocando de endereço dentro dela.
    """
    if proxies_confiaveis > 0:
        enderecos = [e.strip() for cabecalho in cabecalhos_xff for e in cabecalho.split(",")]
        if len(enderecos) >= proxies_confiaveis:
            chave = _chave_do_ip(enderecos[-proxies_confiaveis])
            if chave is not None:
                return chave
    if ip_conexao is None:
        return "sem-ip"
    # Fora do Cloud Run (ex.: o TestClient, que se apresenta como "testclient"), o valor da
    # conexão pode não ser um IP: fica como veio.
    return _chave_do_ip(ip_conexao) or ip_conexao


def _chave_do_ip(endereco: str) -> str | None:
    """O IPv4 como está; o IPv6, pela rede /64 (o IPv4 escrito como IPv6 vira o IPv4). None se
    não for um IP."""
    try:
        ip = ipaddress.ip_address(endereco)
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv4Address):
        return str(ip)
    if ip.ipv4_mapped is not None:
        return str(ip.ipv4_mapped)
    # Pelo número, para ignorar o identificador de zona (fe80::1%eth0) que o ip_network recusa.
    return str(ipaddress.IPv6Network((int(ip) >> 64 << 64, 64)))


class LimitadorPorJanela:
    """Até `limite` chamadas por chave em qualquer intervalo de `janela_s` segundos.

    Chamadas recusadas não contam. Quando há mais de `limpar_acima_de` chaves, as inativas são
    esquecidas antes de uma chave nova entrar, para a memória não crescer sem fim.
    """

    def __init__(
        self,
        limite: int,
        janela_s: float,
        relogio: Callable[[], float] = time.monotonic,
        limpar_acima_de: int = 10_000,
    ) -> None:
        self.limite = limite
        self.janela_s = janela_s
        self._relogio = relogio
        self._limpar_acima_de = limpar_acima_de
        self._chamadas: dict[str, deque[float]] = {}
        self._trava = threading.Lock()

    def __len__(self) -> int:
        return len(self._chamadas)

    def permitir(self, chave: str) -> bool:
        with self._trava:
            agora = self._relogio()
            if chave not in self._chamadas and len(self._chamadas) >= self._limpar_acima_de:
                self._esquecer_inativas(agora)
            fila = self._chamadas.setdefault(chave, deque())
            self._descartar_antigas(fila, agora)
            if len(fila) >= self.limite:
                return False
            fila.append(agora)
            return True

    def espera(self, chave: str) -> int:
        """Segundos inteiros até a chave poder chamar de novo (0 se já pode)."""
        with self._trava:
            fila = self._chamadas.get(chave)
            if not fila:
                return 0
            agora = self._relogio()
            self._descartar_antigas(fila, agora)
            if len(fila) < self.limite:
                return 0
            return max(1, math.ceil(self.janela_s - (agora - fila[0])))

    def _descartar_antigas(self, fila: deque[float], agora: float) -> None:
        while fila and agora - fila[0] >= self.janela_s:
            fila.popleft()

    def _esquecer_inativas(self, agora: float) -> None:
        inativas = [c for c, f in self._chamadas.items() if not f or agora - f[-1] >= self.janela_s]
        for chave in inativas:
            del self._chamadas[chave]


class ServidorOcupado(Exception):
    """Todas as vagas de análise estão em uso."""


class LimiteDeAnalises:
    """No máximo `maximo` análises ao mesmo tempo; acima disso recusa na hora, sem fila."""

    def __init__(self, maximo: int) -> None:
        self.maximo = maximo
        self._vagas = threading.BoundedSemaphore(maximo)

    @contextmanager
    def vaga(self) -> Iterator[None]:
        if not self._vagas.acquire(blocking=False):
            raise ServidorOcupado
        try:
            yield
        finally:
            self._vagas.release()


class LimiteDeCorpo:
    """Middleware ASGI: recusa com 413 corpos acima de `maximo` bytes.

    Pelo Content-Length, antes de ler qualquer byte; sem ele (corpo em partes), contando o que
    chega e interrompendo a leitura assim que passa do limite.
    """

    def __init__(self, app: ASGIApp, maximo: int) -> None:
        self.app = app
        self.maximo = maximo

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declarado = Headers(scope=scope).get("content-length", "")
        if declarado.isdigit() and int(declarado) > self.maximo:
            resposta = JSONResponse(
                status_code=413, content={"detail": {"codigo": "corpo_grande_demais"}}
            )
            await resposta(scope, receive, send)
            return

        recebidos = 0

        async def receber() -> Message:
            nonlocal recebidos
            mensagem = await receive()
            if mensagem["type"] == "http.request":
                recebidos += len(mensagem.get("body", b""))
                if recebidos > self.maximo:
                    raise HTTPException(413, detail={"codigo": "corpo_grande_demais"})
            return mensagem

        await self.app(scope, receber, send)


CSP = "default-src 'none'; frame-ancestors 'none'"
HSTS = "max-age=63072000; includeSubDomains"


class CabecalhosDeSeguranca:
    """Middleware ASGI: cabeçalhos de segurança em toda resposta.

    A API só devolve JSON, então a CSP proíbe tudo. As páginas de documentação (só existem em
    desenvolvimento) ficam sem CSP porque carregam scripts externos. O HSTS só vale em produção,
    atrás de HTTPS. Uma rota pode definir o próprio Cache-Control; os demais são fixos.
    """

    def __init__(self, app: ASGIApp, hsts: bool, documentacao: bool) -> None:
        self.app = app
        self.hsts = hsts
        self.sem_csp = ("/docs", "/redoc") if documentacao else ()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        com_csp = not scope["path"].startswith(self.sem_csp) if self.sem_csp else True

        async def enviar(mensagem: Message) -> None:
            if mensagem["type"] == "http.response.start":
                cabecalhos = MutableHeaders(scope=mensagem)
                cabecalhos["X-Content-Type-Options"] = "nosniff"
                cabecalhos["Referrer-Policy"] = "no-referrer"
                cabecalhos["X-Frame-Options"] = "DENY"
                cabecalhos.setdefault("Cache-Control", "no-store")
                if com_csp:
                    cabecalhos["Content-Security-Policy"] = CSP
                if self.hsts:
                    cabecalhos["Strict-Transport-Security"] = HSTS
            await send(mensagem)

        await self.app(scope, receive, enviar)
