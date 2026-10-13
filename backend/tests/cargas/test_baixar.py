"""Download das cargas, sem rede: a resposta do servidor é simulada."""

import io

import pytest

from cargas.baixar import ErroDeDownload, baixar

PORTAL = "https://dados.exemplo/dados/"


class RespostaFalsa(io.BytesIO):
    """Imita a resposta do urllib: o conteúdo e o endereço final (depois de redirecionamentos)."""

    def __init__(self, conteudo: bytes, endereco_final: str) -> None:
        super().__init__(conteudo)
        self.endereco_final = endereco_final

    def geturl(self) -> str:
        return self.endereco_final


def servidor(conteudo: bytes = b"zip", endereco_final: str | None = None):
    pedidos = []

    def abrir(pedido, timeout):
        pedidos.append((pedido.full_url, timeout))
        return RespostaFalsa(conteudo, endereco_final or pedido.full_url)

    return abrir, pedidos


def test_baixa_o_arquivo_do_endereco_permitido():
    abrir, pedidos = servidor(b"conteudo")

    assert baixar(PORTAL + "a.zip", PORTAL, abrir=abrir) == b"conteudo"
    assert pedidos == [(PORTAL + "a.zip", 120)]


@pytest.mark.parametrize(
    "url", ["https://outro.exemplo/dados/a.zip", "http://dados.exemplo/dados/a.zip"]
)
def test_recusa_endereco_fora_do_permitido(url):
    abrir, pedidos = servidor()

    with pytest.raises(ValueError, match="fora do endereço permitido"):
        baixar(url, PORTAL, abrir=abrir)
    assert pedidos == []


def test_recusa_endereco_permitido_que_nao_e_https():
    abrir, _ = servidor()

    with pytest.raises(ValueError, match="https"):
        baixar("http://dados.exemplo/a.zip", "http://dados.exemplo/", abrir=abrir)


def test_recusa_redirecionamento_para_fora_do_permitido():
    abrir, _ = servidor(endereco_final="https://outro.exemplo/a.zip")

    with pytest.raises(ErroDeDownload, match="redirecionado"):
        baixar(PORTAL + "a.zip", PORTAL, abrir=abrir)


def test_recusa_arquivo_maior_que_o_limite():
    abrir, _ = servidor(b"x" * 11)

    with pytest.raises(ErroDeDownload, match="maior que 10 bytes"):
        baixar(PORTAL + "a.zip", PORTAL, abrir=abrir, maximo=10)
