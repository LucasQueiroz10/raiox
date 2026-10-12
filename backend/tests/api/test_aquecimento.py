"""Aquecimento interno (ADR 0007, seção 3): o Cloud Scheduler chama depois da carga da CDA, para
nenhum usuário pagar a releitura. Fica fora do /api (o Firebase não encaminha), exige um segredo no
cabeçalho e responde 404 sem ele, como se não existisse. Não devolve dados."""

from fastapi.testclient import TestClient

from app.config import Config
from app.main import CABECALHO_AQUECIMENTO, criar_app

SEGREDO = "segredo-sintetico-de-teste-com-mais-de-32-caracteres"


class DadosFalsos:
    def __init__(self, pronto: bool = True) -> None:
        self.pronto = pronto
        self.aquecimentos = 0

    def foto(self):
        raise AssertionError("o aquecimento não lê a foto pela análise")

    def aquecer(self) -> bool:
        self.aquecimentos += 1
        return self.pronto


def _cliente(segredo: str | None = SEGREDO, dados=None) -> tuple[TestClient, DadosFalsos]:
    app = criar_app(Config(producao=False, origens_permitidas=(), segredo_aquecimento=segredo))
    app.state.dados = dados = dados or DadosFalsos()
    return TestClient(app), dados


def test_com_o_segredo_aquece_e_nao_devolve_dados():
    cliente, dados = _cliente()

    r = cliente.post("/interno/aquecer", headers={CABECALHO_AQUECIMENTO: SEGREDO})

    assert r.status_code == 204
    assert r.content == b""
    assert dados.aquecimentos == 1


def test_sem_o_cabecalho_ou_com_o_errado_responde_404_sem_aquecer():
    cliente, dados = _cliente()

    sem = cliente.post("/interno/aquecer")
    errado = cliente.post("/interno/aquecer", headers={CABECALHO_AQUECIMENTO: SEGREDO + "x"})

    assert sem.status_code == errado.status_code == 404
    assert sem.json() == errado.json() == cliente.post("/nao/existe").json()
    assert dados.aquecimentos == 0


def test_sem_segredo_configurado_o_aquecimento_nao_existe():
    cliente, dados = _cliente(segredo=None)

    r = cliente.post("/interno/aquecer", headers={CABECALHO_AQUECIMENTO: SEGREDO})

    assert r.status_code == 404
    assert dados.aquecimentos == 0


def test_sem_dados_depois_de_aquecer_responde_503():
    cliente, _ = _cliente(dados=DadosFalsos(pronto=False))

    r = cliente.post("/interno/aquecer", headers={CABECALHO_AQUECIMENTO: SEGREDO})

    assert r.status_code == 503
    assert r.json() == {"detail": {"codigo": "dados_indisponiveis"}}


def test_aquecimento_fica_fora_do_api_e_do_contrato():
    cliente, dados = _cliente()

    r = cliente.post("/api/interno/aquecer", headers={CABECALHO_AQUECIMENTO: SEGREDO})
    caminhos = cliente.app.openapi()["paths"]

    assert r.status_code == 404
    assert dados.aquecimentos == 0
    assert not any("aquecer" in c for c in caminhos)
