"""Download dos arquivos públicos das cargas, com limites.

As cargas acessam a internet pela saída padrão do Cloud Run (ADR 0007, seção 5). Cada fonte declara
o endereço permitido (ex.: o portal de dados abertos da CVM) e o download recusa qualquer outro,
inclusive depois de um redirecionamento. O arquivo fica só na memória: nenhum arquivo bruto é
guardado (o do CDA traz CPF de emissores pessoa física; decisão de 12/10/2026, ADR 0008).
"""

import urllib.request
from collections.abc import Callable
from typing import Any

TEMPO_LIMITE_S = 120
# Um mês do CDA tem uns 25 MB; o limite só protege contra uma resposta errada ou maliciosa.
TAMANHO_MAXIMO = 200 * 1024 * 1024
# Sem o nome do produto, que ainda não é público (R-09).
AGENTE = "rx-cargas (dados abertos)"

type Abrir = Callable[..., Any]


class ErroDeDownload(Exception):
    """O download não trouxe o arquivo esperado."""


def baixar(
    url: str,
    permitido: str,
    *,
    abrir: Abrir = urllib.request.urlopen,
    maximo: int = TAMANHO_MAXIMO,
) -> bytes:
    """Baixa `url` e devolve o conteúdo. `url` precisa começar pelo endereço `permitido`, que
    precisa ser https. `abrir` existe para os testes simularem o servidor, sem rede."""
    if not permitido.startswith("https://"):
        raise ValueError("o endereço permitido precisa ser https")
    if not url.startswith(permitido):
        raise ValueError("url fora do endereço permitido")
    # S310: o esquema já foi conferido acima (só https, só o endereço da fonte).
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})  # noqa: S310
    with abrir(pedido, timeout=TEMPO_LIMITE_S) as resposta:
        if not resposta.geturl().startswith(permitido):
            raise ErroDeDownload("download redirecionado para fora do endereço permitido")
        # Lê um byte além do limite: se vier, o arquivo é grande demais.
        conteudo = resposta.read(maximo + 1)
    if len(conteudo) > maximo:
        raise ErroDeDownload(f"arquivo maior que {maximo} bytes")
    return conteudo
