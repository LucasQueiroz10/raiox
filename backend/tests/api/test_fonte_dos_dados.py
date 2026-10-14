"""De onde a API tira os dados públicos: banco ou conjunto de exemplo (ADR 0006)."""

from fastapi.testclient import TestClient

from app.config import Config
from app.dados.exemplo import RepositorioExemplo
from app.dados.postgres import DadosIndisponiveis, RepositorioPostgres
from app.main import criar_app

CARTEIRA = {
    "posicoes": [
        {
            "tipo_identificador": "isin",
            "identificador": "ZZBANCO00013",
            "valor": "500.00",
            "moeda": "BRL",
            "tipo": "acao",
        }
    ]
}
# Porta 1: nada escuta nela, então a conexão é recusada na hora.
BANCO_FORA_DO_AR = "postgresql+psycopg://rx_api@127.0.0.1:1/rx"


def _config(banco_url: str | None = None) -> Config:
    return Config(producao=False, origens_permitidas=(), banco_url=banco_url)


def test_sem_banco_a_api_usa_o_conjunto_de_exemplo():
    app = criar_app(_config())

    resposta = TestClient(app).post("/api/raiox", json=CARTEIRA)

    assert isinstance(app.state.dados, RepositorioExemplo)
    assert resposta.status_code == 200
    assert resposta.json()["versao_classificacao"] == "exemplo-v1"


def test_com_banco_a_api_usa_o_postgres_e_nao_conecta_na_partida():
    app = criar_app(_config(BANCO_FORA_DO_AR))

    assert isinstance(app.state.dados, RepositorioPostgres)


def test_banco_fora_do_ar_sem_dados_lidos_responde_503():
    with TestClient(criar_app(_config(BANCO_FORA_DO_AR))) as cliente:
        resposta = cliente.post("/api/raiox", json=CARTEIRA)

    assert resposta.status_code == 503
    assert resposta.json() == {"detail": {"codigo": "dados_indisponiveis"}}


class DadosQueFalham:
    def __init__(self) -> None:
        self.fotos = 0

    def foto(self):
        self.fotos += 1
        raise DadosIndisponiveis("simulado")


def test_cada_analise_pede_uma_foto_so_dos_dados():
    app = criar_app(_config())
    app.state.dados = dados = DadosQueFalham()

    resposta = TestClient(app).post("/api/raiox", json=CARTEIRA)

    assert resposta.status_code == 503
    assert dados.fotos == 1
