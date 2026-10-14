"""POST /raiox lendo o banco (ADR 0006): a mesma resposta do conjunto de exemplo restrito às
linhas aprovadas da classificação, que são as únicas que o banco mostra."""

from dataclasses import replace

from fastapi.testclient import TestClient

from app.config import Config
from app.core.classificacao import Status, TabelaClassificacao
from app.dados.exemplo import RepositorioExemplo
from app.main import criar_app
from tests.banco.apoio import carregar_exemplo

# Carteira de referência de tests/api/test_raiox.py: fundo de fundos e uma ação direta.
CARTEIRA = {
    "posicoes": [
        {"isin": "ZZFOF0000016", "valor": "1000.00", "moeda": "BRL", "tipo": "fundo"},
        {"isin": "ZZBANCO00013", "valor": "500.00", "moeda": "BRL", "tipo": "acao"},
    ]
}


class ExemploSoAprovado:
    """O conjunto de exemplo como o banco o mostra: sem setores nem temas em rascunho."""

    def __init__(self) -> None:
        self._exemplo = RepositorioExemplo()
        tabela = self._exemplo.tabela_classificacao()
        self.rascunhos = sum(
            (c.setor_status is Status.RASCUNHO) + sum(t.status is Status.RASCUNHO for t in c.temas)
            for c in tabela.classificacoes.values()
        )
        self._tabela = TabelaClassificacao(
            tabela.versao,
            {
                e: replace(c, temas=tuple(t for t in c.temas if t.status is Status.APROVADO))
                for e, c in tabela.classificacoes.items()
                if c.setor_status is Status.APROVADO
            },
        )

    def foto(self):
        return self

    def aquecer(self):
        return True

    def identificacao(self):
        return self._exemplo.identificacao()

    def composicoes(self):
        return self._exemplo.composicoes()

    def empresa_do_ativo(self):
        return self._exemplo.empresa_do_ativo()

    def tabela_classificacao(self):
        return self._tabela

    def nome(self, identificador):
        return self._exemplo.nome(identificador)


def _analisar(config: Config, dados=None) -> dict:
    app = criar_app(config)
    if dados is not None:
        app.state.dados = dados
    with TestClient(app) as cliente:
        resposta = cliente.post("/api/raiox", json=CARTEIRA)
    assert resposta.status_code == 200
    corpo = resposta.json()
    del corpo["versao_classificacao"]  # a do banco vem da carga publicada
    return corpo


def test_raiox_lendo_o_banco_responde_como_o_exemplo_so_com_linhas_aprovadas(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao:
        carregar_exemplo(ingestao)
    esperado = ExemploSoAprovado()
    config = Config(producao=False, origens_permitidas=())

    do_banco = _analisar(replace(config, banco_url=banco_novo.url("rx_api")))

    assert esperado.rascunhos  # o exemplo tem linhas preliminares, então o filtro faz diferença
    assert do_banco == _analisar(config, esperado)
    assert do_banco != _analisar(config)
