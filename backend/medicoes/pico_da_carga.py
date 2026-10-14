"""Mede o pico de memória de uma carga, para dimensionar o Cloud Run Job (ADR 0007, seção 5).

Roda a carga neste mesmo processo, pelo mesmo caminho do job (o main() de cargas.cvm ou de
cargas.cadastro), e no fim imprime o retorno, o tempo e o pico de memória do processo: o maior
working set no Windows e o maior RSS no Linux. Nada dos dados. Não roda no CI.

A carga publica de verdade no banco de RX_BANCO_URL. Por isso o script só aceita um banco no
próprio computador (127.0.0.1 ou localhost), nunca o de produção (revisão do PR #70).

Uso, dentro de backend/, com o banco local (docker compose up -d --wait):
    export RX_BANCO_URL=postgresql+psycopg://rx_ingestao@127.0.0.1:5433/rx
    python -m medicoes.pico_da_carga cadastro               baixa as fontes do portal da CVM
    python -m medicoes.pico_da_carga cadastro --pasta DIR   lê os zips já baixados
    python -m medicoes.pico_da_carga cvm --meses 3
"""

import ctypes
import os
import sys
import time
from collections.abc import Callable

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from cargas import cadastro, cvm

CARGAS: dict[str, Callable[[list[str]], int]] = {"cvm": cvm.main, "cadastro": cadastro.main}
LOCAIS = {"127.0.0.1", "localhost"}


def banco_local(url: str | None) -> bool:
    """Diz se a URL aponta, com certeza, para um banco no próprio computador. Recusa a URL sem host
    (o libpq usaria o PGHOST ou o socket) e a com host ou hostaddr na consulta (passam por cima do
    host da URL)."""
    if not url:
        return False
    try:
        partes = make_url(url)
    except ArgumentError:
        return False
    if {"host", "hostaddr"} & set(partes.query):
        return False
    return (partes.host or "").lower() in LOCAIS


def _pico_windows() -> int:
    """O maior working set do processo, em bytes (GetProcessMemoryInfo, da psapi)."""
    from ctypes import wintypes

    class Contadores(ctypes.Structure):
        _fields_ = [  # noqa: RUF012 - formato fixo da estrutura PROCESS_MEMORY_COUNTERS
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    contadores = Contadores()
    contadores.cb = ctypes.sizeof(contadores)
    kernel32 = ctypes.WinDLL("kernel32")
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi")
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(Contadores),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(contadores), contadores.cb
    )
    return contadores.PeakWorkingSetSize


def pico_de_memoria_mb() -> float:
    """O pico de memória do processo até agora, em MB."""
    if sys.platform == "win32":
        return _pico_windows() / 2**20
    import resource

    # No Linux, ru_maxrss vem em KiB.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**10


def main(argv: list[str] | None = None) -> int:
    """Devolve o retorno da carga, ou 2 se o uso estiver errado ou o banco não for local."""
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] not in CARGAS:
        print(
            "uso: python -m medicoes.pico_da_carga {cvm|cadastro} [opções da carga]",
            file=sys.stderr,
        )
        return 2
    if not banco_local(os.environ.get("RX_BANCO_URL")):
        # Sem repetir a URL: ela pode trazer o endereço e a senha de um banco de verdade.
        print(
            "Recusado: esta medição publica cargas de verdade, e RX_BANCO_URL precisa apontar"
            " para um banco no próprio computador (127.0.0.1 ou localhost).",
            file=sys.stderr,
        )
        return 2
    inicio = time.perf_counter()
    retorno = CARGAS[args[0]](args[1:])
    segundos = time.perf_counter() - inicio
    print(
        f"carga {args[0]}: retorno {retorno}, {segundos:.0f} s,"
        f" pico de memória do processo {pico_de_memoria_mb():.0f} MB"
    )
    return retorno


if __name__ == "__main__":
    sys.exit(main())
