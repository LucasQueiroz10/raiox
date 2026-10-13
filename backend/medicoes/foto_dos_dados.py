"""Mede a foto dos dados da API (DT-10): quanto tempo e quanta memória a leitura das visões vigentes
leva com o que estiver publicado no banco.

Lê pelo mesmo caminho da API (app/dados/postgres.ler_foto), como rx_api. Imprime só contagens,
tempo e memória: nada dos dados. Não roda no CI. Uso, dentro de backend/, com o banco carregado
(ex.: python -m cargas.cvm --meses 3):
    export RX_BANCO_URL=postgresql+psycopg://rx_api@127.0.0.1:5433/rx
    python -m medicoes.foto_dos_dados
"""

import os
import sys
import time
import tracemalloc

from sqlalchemy import create_engine

from app.dados.postgres import ler_foto


def main() -> None:
    url = os.environ.get("RX_BANCO_URL")
    if not url:
        sys.exit("Defina RX_BANCO_URL com o usuário rx_api.")
    motor = create_engine(url)
    with motor.connect() as conexao:
        tracemalloc.start()
        inicio = time.perf_counter()
        foto = ler_foto(conexao)
        segundos = time.perf_counter() - inicio
        atual, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    composicoes = foto.composicoes()
    itens = sum(len(c.itens) for c in composicoes.values())
    print(f"composições: {len(composicoes)} | itens: {itens}")
    print(f"tempo da leitura: {segundos:.1f} s")
    # Durante a releitura há duas fotos na memória (a antiga segue servindo): conta em dobro.
    print(f"memória da foto: {atual / 2**20:.0f} MB (pico da leitura: {pico / 2**20:.0f} MB)")
    print(f"na releitura, com duas fotos: cerca de {2 * atual / 2**20:.0f} MB")


if __name__ == "__main__":
    main()
