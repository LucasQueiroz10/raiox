"""Carga do cadastro (ADR 0008, etapa 4): identificação e setor oficial, com fontes sintéticas nos
formatos da CVM, rodando como rx_ingestao. Cada teste usa um banco novo."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.main import criar_app
from cargas.cadastro import Fontes, carregar_cadastro
from cargas.rotina import ErroDeValidacao
from ingest.arquivos_cvm import LayoutInesperado
from ingest.cvm_fca import COLUNAS
from tests.ficticios import cnpj, isin_da_raiz
from tests.ingest.cda_sintetico import MesSintetico
from tests.ingest.fca_sintetico import AnoSintetico
from tests.ingest.fii_sintetico import AnoFII

EMPRESA, ETF, FII, FUNDO = (cnpj(f"CADASTRO-{n}") for n in ("EMPRESA", "ETF", "FII", "FUNDO"))
ON, PN = isin_da_raiz("ZZAA", "ACNOR"), isin_da_raiz("ZZAA", "ACNPR")
ISIN_DO_FII = isin_da_raiz("ZZFI", "CTF00")


@pytest.fixture
def curadoria_vazia(tmp_path: Path) -> Path:
    (tmp_path / "emissores_b3.csv").write_text("raiz;cnpj;nome;motivo\n", encoding="utf-8")
    (tmp_path / "fundos_listados.csv").write_text("ticker;cnpj;nome;fonte\n", encoding="utf-8")
    return tmp_path


def fontes(curadoria: Path, *tickers_extras: str, colunas_fca=None) -> Fontes:
    """Uma companhia com ON e PN (o CDA traz o ISIN das duas, que um fundo tem), um ETF emprestado
    e um FII de tijolo."""
    fca = AnoSintetico().companhia(EMPRESA, "ZZAA3", "ZZAA4", *tickers_extras)
    cda = (
        MesSintetico()
        .patrimonio(FUNDO, "1000.00")
        .aplicacao("fi_BLC_4", FUNDO, "Ações", "100.00", CD_ATIVO="ZZAA3", CD_ISIN=ON)
        .aplicacao("fi_BLC_4", FUNDO, "Ações", "100.00", CD_ATIVO="ZZAA4", CD_ISIN=PN)
        .aplicacao(
            "fi_BLC_8",
            FUNDO,
            "Ações e outros TVM cedidos em empréstimo",
            "1.00",
            TP_ATIVO="Fundos de Índice",
            DS_ATIVO="ZZTF11 - ETF",
            PF_PJ_EMISSOR="PJ",
            CPF_CNPJ_EMISSOR=ETF,
        )
    )
    fii = AnoFII().fundo(FII, isin=ISIN_DO_FII, nome="FII SINTETICO", Direitos_Bens_Imoveis="1")
    return Fontes(
        fca=[fca.zip(colunas=colunas_fca)], cda=[cda.zip()], fii=[fii.zip()], curadoria=curadoria
    )


def cargas(conexao) -> list[tuple]:
    return conexao.execute("SELECT tipo, status FROM ref.carga ORDER BY carga_id").fetchall()


def test_cadastro_publica_identificacao_e_setor_e_a_api_soma_as_classes(
    banco_novo, curadoria_vazia
):
    with banco_novo.conectar("rx_ingestao") as ingestao, banco_novo.conectar("rx_api") as api:
        relatorio = carregar_cadastro(ingestao, fontes(curadoria_vazia))

        assert cargas(ingestao) == [("identificacao", "publicada"), ("classificacao", "publicada")]
        assert (relatorio.empresas, relatorio.setores) == (1, 1)
        ativos = {
            linha[0]: linha[1:]
            for linha in api.execute(
                "SELECT ativo_id, tipo, empresa_id, ticker_b3, fii_tipo, fii_segmento"
                " FROM ref.ativo_vigente"
            )
        }
        assert ativos == {
            ON: ("acao", f"BR:CNPJ:{EMPRESA}", "ZZAA3", None, None),
            PN: ("acao", f"BR:CNPJ:{EMPRESA}", "ZZAA4", None, None),
            f"CNPJ:{ETF}": ("fundo", None, "ZZTF11", None, None),
            f"CNPJ:{FII}": ("fundo", None, None, "tijolo", "Logística"),
        }
        setores = api.execute(
            "SELECT empresa_id, setor, setor_origem, setor_status FROM ref.classificacao_vigente"
        ).fetchall()
        assert setores == [(f"BR:CNPJ:{EMPRESA}", "Setor Sintético", "oficial", "aprovado")]

    # Ponta a ponta: as duas classes da mesma companhia somam numa empresa só, com o setor (DT-3).
    config = Config(producao=False, origens_permitidas=(), banco_url=banco_novo.url("rx_api"))
    carteira = {
        "posicoes": [
            {"isin": ON, "valor": "100.00", "moeda": "BRL", "tipo": "acao"},
            {"isin": PN, "valor": "50.00", "moeda": "BRL", "tipo": "acao"},
        ]
    }
    with TestClient(criar_app(config)) as cliente:
        corpo = cliente.post("/api/raiox", json=carteira).json()

    (empresa,) = corpo["empresas"]
    assert (empresa["empresa_id"], empresa["setor"], empresa["total"]) == (
        f"BR:CNPJ:{EMPRESA}",
        "Setor Sintético",
        "150.00",
    )
    assert [c["ativo_id"] for c in empresa["classes"]] == [ON, PN]


def test_queda_grande_no_numero_de_ativos_nao_publica(banco_novo, curadoria_vazia):
    extras = [f"ZZA{letra}3" for letra in "BCDEFGHIJK"]
    with banco_novo.conectar("rx_ingestao") as ingestao:
        carregar_cadastro(ingestao, fontes(curadoria_vazia, *extras))

        with pytest.raises(ErroDeValidacao, match="ativos"):
            carregar_cadastro(ingestao, fontes(curadoria_vazia))

        assert cargas(ingestao)[2:] == [("identificacao", "com_erro")]


def test_fonte_com_formato_novo_fica_com_erro_e_nada_e_publicado(banco_novo, curadoria_vazia):
    sem_setor = tuple(c for c in COLUNAS["geral"] if c != "Setor_Atividade")
    with banco_novo.conectar("rx_ingestao") as ingestao:
        with pytest.raises(LayoutInesperado):
            carregar_cadastro(ingestao, fontes(curadoria_vazia, colunas_fca={"geral": sem_setor}))

        assert cargas(ingestao) == [("identificacao", "com_erro")]


def test_curadoria_com_linha_errada_fica_com_erro(banco_novo, curadoria_vazia):
    (curadoria_vazia / "emissores_b3.csv").write_text(
        "raiz;cnpj;nome;motivo\nZZAA;12345678000100;NOME;teste\n", encoding="utf-8"
    )
    with banco_novo.conectar("rx_ingestao") as ingestao:
        with pytest.raises(ValueError, match="CNPJ inválido"):
            carregar_cadastro(ingestao, fontes(curadoria_vazia))

        assert cargas(ingestao) == [("identificacao", "com_erro")]
