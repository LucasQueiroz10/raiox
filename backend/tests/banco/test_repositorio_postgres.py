"""RepositorioPostgres: lê das visões vigentes os mesmos dados que o RepositorioExemplo entrega.

Cada teste usa um banco novo (banco_novo), porque o que vale é a última foto publicada.
"""

from collections.abc import Iterator
from dataclasses import replace
from datetime import date
from decimal import Decimal

import psycopg
import pytest
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.core.classificacao import Origem, ParticipacaoTema, Status
from app.core.composicao import ItemComposicao, TipoItem
from app.dados.exemplo import RepositorioExemplo
from app.dados.postgres import (
    INTERVALO_S,
    SEM_CLASSIFICACAO,
    DadosIndisponiveis,
    RepositorioPostgres,
)
from app.dados.repositorio import RepositorioDados
from banco.preparar import url_libpq
from tests.banco.apoio import (
    BancoDeTeste,
    abrir_carga,
    carregar_exemplo,
    inserir_composicao,
    publicar,
)
from tests.ficticios import isin

UCITS = "IEZZUCITS001"  # ISIN sintético de ETF UCITS (IE é da lista permitida; ZZ, não)
ETF_EUA = "US:ZZETF"
LEI_ANTIGO = "LEI:ZZZZZZZZZZZZZZZZZZ00"


class Relogio:
    def __init__(self) -> None:
        self.agora = 0.0

    def __call__(self) -> float:
        return self.agora


@pytest.fixture
def relogio() -> Relogio:
    return Relogio()


@pytest.fixture
def repo(banco_novo: BancoDeTeste, relogio: Relogio) -> Iterator[RepositorioPostgres]:
    """Repositório que entra como rx_api, o usuário da API."""
    motor = create_engine(banco_novo.url("rx_api"))
    yield RepositorioPostgres(motor, relogio=relogio)
    motor.dispose()


@pytest.fixture
def ingestao(banco_novo: BancoDeTeste) -> Iterator[psycopg.Connection]:
    with banco_novo.conectar("rx_ingestao") as conexao:
        yield conexao


def _identificacao(ingestao: psycopg.Connection, empresas=(), ativos=(), apelidos=()) -> None:
    carga = abrir_carga(ingestao, "identificacao")
    for empresa_id, nome in empresas:
        ingestao.execute(
            "INSERT INTO ref.empresa (carga_id, empresa_id, nome) VALUES (%s, %s, %s)",
            (carga, empresa_id, nome),
        )
    for ativo_id, tipo, empresa_id, nome, aproximado_por in ativos:
        ingestao.execute(
            "INSERT INTO ref.ativo (carga_id, ativo_id, tipo, empresa_id, nome, aproximado_por)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (carga, ativo_id, tipo, empresa_id, nome, aproximado_por),
        )
    for apelido, empresa_id in apelidos:
        ingestao.execute(
            "INSERT INTO ref.empresa_apelido (carga_id, apelido, empresa_id) VALUES (%s, %s, %s)",
            (carga, apelido, empresa_id),
        )
    publicar(ingestao, carga)


def _classificacao(ingestao: psycopg.Connection, setores=(), temas=()) -> None:
    carga = abrir_carga(ingestao, "classificacao")
    for empresa_id, setor in setores:
        ingestao.execute(
            "INSERT INTO ref.classificacao"
            " (carga_id, empresa_id, setor, setor_origem, setor_status)"
            " VALUES (%s, %s, %s, 'oficial', 'aprovado')",
            (carga, empresa_id, setor),
        )
    for empresa_id, subtema, peso, origem, status in temas:
        ingestao.execute(
            "INSERT INTO ref.classificacao_tema"
            " (carga_id, empresa_id, tema, subtema, peso, origem, status)"
            " VALUES (%s, %s, 'Cadeia de IA', %s, %s, %s, %s)",
            (carga, empresa_id, subtema, Decimal(peso), origem, status),
        )
    publicar(ingestao, carga)


# --- Contrato: os mesmos dados do RepositorioExemplo ---


def test_implementa_o_repositorio(repo):
    assert isinstance(repo, RepositorioDados)


def test_le_as_mesmas_composicoes_ligacoes_e_nomes_do_exemplo(repo, ingestao):
    carregar_exemplo(ingestao)
    exemplo = RepositorioExemplo()
    ligacao = exemplo.empresa_do_ativo()
    nomeados = set(ligacao) | set(ligacao.values()) | set(exemplo.composicoes())

    assert repo.composicoes() == exemplo.composicoes()
    assert repo.empresa_do_ativo() == ligacao
    assert {i: repo.nome(i) for i in nomeados} == {i: exemplo.nome(i) for i in nomeados}
    assert repo.nome("ZZ0000000000") is None


def test_le_a_classificacao_do_exemplo_so_com_as_linhas_aprovadas(repo, ingestao):
    carregar_exemplo(ingestao)
    exemplo = RepositorioExemplo().tabela_classificacao().classificacoes
    rascunhos = [t for c in exemplo.values() for t in c.temas if t.status is Status.RASCUNHO]
    esperado = {
        e: replace(c, temas=tuple(t for t in c.temas if t.status is Status.APROVADO))
        for e, c in exemplo.items()
        if c.setor_status is Status.APROVADO
    }

    assert rascunhos  # o exemplo tem linhas preliminares, que o banco não mostra
    assert dict(repo.tabela_classificacao().classificacoes) == esperado


# --- Regras do repositório ---


def test_tema_aprovado_chega_com_origem_e_peso_exato(repo, ingestao):
    _classificacao(
        ingestao,
        setores=[("ZZ:NUVEM", "Tecnologia")],
        temas=[("ZZ:NUVEM", "Nuvem", "0.123456789012345678901234567890", "manual", "aprovado")],
    )

    classificacao = repo.tabela_classificacao().classificacoes["ZZ:NUVEM"]

    assert classificacao.temas == (
        ParticipacaoTema(
            "Cadeia de IA",
            "Nuvem",
            Decimal("0.123456789012345678901234567890"),
            origem=Origem.MANUAL,
            status=Status.APROVADO,
        ),
    )


def test_versao_da_classificacao_muda_a_cada_publicacao(repo, ingestao, relogio):
    assert repo.tabela_classificacao().versao == SEM_CLASSIFICACAO

    _classificacao(ingestao, setores=[("ZZ:BANCO", "Financeiro")])
    relogio.agora += INTERVALO_S
    primeira = repo.tabela_classificacao().versao
    _classificacao(ingestao, setores=[("ZZ:BANCO", "Financeiro")])
    relogio.agora += INTERVALO_S
    segunda = repo.tabela_classificacao().versao

    assert SEM_CLASSIFICACAO not in (primeira, segunda)
    assert primeira != segunda


def test_ucits_usa_a_composicao_do_etf_americano_com_rotulo(repo, ingestao):
    _identificacao(
        ingestao,
        ativos=[
            (ETF_EUA, "fundo", None, "ETF Sintético EUA", None),
            (UCITS, "fundo", None, "ETF Sintético UCITS", ETF_EUA),
        ],
    )
    carga = abrir_carga(ingestao, "composicoes_nport", date(2026, 6, 30))
    inserir_composicao(ingestao, carga, ETF_EUA, date(2026, 6, 30), [(isin("U1"), "1", "acao")])
    publicar(ingestao, carga)

    composicoes = repo.composicoes()

    assert composicoes[UCITS] == replace(
        composicoes[ETF_EUA], fundo_id=UCITS, aproximado_por=ETF_EUA
    )
    assert repo.nome(UCITS) == "ETF Sintético UCITS"


def test_apelido_leva_item_e_classificacao_para_a_empresa_atual(repo, ingestao):
    _identificacao(
        ingestao, empresas=[("ZZ:NOVA", "Empresa Sintética")], apelidos=[(LEI_ANTIGO, "ZZ:NOVA")]
    )
    _classificacao(ingestao, setores=[(LEI_ANTIGO, "Tecnologia")])
    carga = abrir_carga(ingestao, "composicoes_nport", date(2026, 6, 30))
    composicao = ingestao.execute(
        "INSERT INTO ref.composicao (carga_id, fundo_id, data_referencia, moeda)"
        " VALUES (%s, %s, %s, 'USD') RETURNING composicao_id",
        (carga, ETF_EUA, date(2026, 6, 30)),
    ).fetchone()[0]
    ingestao.execute(
        "INSERT INTO ref.composicao_item (composicao_id, ordem, empresa_id, tipo, peso, emissor)"
        " VALUES (%s, 1, %s, 'acao', 0.6, NULL), (%s, 2, NULL, 'credito', 0.4, %s)",
        (composicao, LEI_ANTIGO, composicao, LEI_ANTIGO),
    )
    publicar(ingestao, carga)

    itens = repo.composicoes()[ETF_EUA].itens
    tabela = repo.tabela_classificacao().classificacoes

    assert itens == (
        ItemComposicao(None, Decimal("0.6"), TipoItem.ACAO, empresa_id="ZZ:NOVA"),
        ItemComposicao(None, Decimal("0.4"), TipoItem.CREDITO, emissor="ZZ:NOVA"),
    )
    assert set(tabela) == {"ZZ:NOVA"}
    assert tabela["ZZ:NOVA"].empresa_id == "ZZ:NOVA"


def test_nome_do_fundo_sem_identificacao_vem_da_composicao(repo, ingestao):
    fundo = "CNPJ:11222333000009"
    carga = abrir_carga(ingestao, "composicoes_cvm", date(2026, 8, 31))
    inserir_composicao(ingestao, carga, fundo, date(2026, 8, 31), [(isin("N1"), "1", "acao")])
    publicar(ingestao, carga)

    assert repo.nome(fundo) == "Fundo Sintético"


# --- Foto em memória ---


def test_so_rele_quando_sai_carga_nova(repo, ingestao, relogio):
    carregar_exemplo(ingestao)
    primeira = repo.foto()

    relogio.agora += INTERVALO_S
    assert repo.foto() is primeira  # conferiu e não saiu nada novo

    fundo = "CNPJ:ZZ998877000008"
    carga = abrir_carga(ingestao, "composicoes_cvm", date(2026, 9, 30))
    inserir_composicao(ingestao, carga, fundo, date(2026, 9, 30), [(isin("R1"), "1", "acao")])
    publicar(ingestao, carga)
    assert repo.foto() is primeira  # ainda dentro do intervalo

    relogio.agora += INTERVALO_S
    assert fundo in repo.foto().composicoes()


def test_ptax_nova_nao_obriga_a_reler_a_foto(repo, ingestao, relogio):
    primeira = repo.foto()
    carga = abrir_carga(ingestao, "ptax")
    ingestao.execute(
        "INSERT INTO ref.ptax (carga_id, data_cotacao, valor) VALUES (%s, %s, 5.1)",
        (carga, date(2001, 1, 2)),
    )
    publicar(ingestao, carga)

    relogio.agora += INTERVALO_S
    assert repo.foto() is primeira


def test_banco_fora_do_ar_segue_com_a_ultima_foto(repo, ingestao, relogio, banco_novo, caplog):
    carregar_exemplo(ingestao)
    primeira = repo.foto()
    ingestao.close()
    with psycopg.connect(url_libpq(banco_novo.url_admin), autocommit=True) as admin:
        admin.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(banco_novo.nome))
        )

    relogio.agora += INTERVALO_S
    assert repo.foto() is primeira
    assert "última foto" in caplog.text


def test_sem_banco_na_primeira_leitura_avisa_que_os_dados_estao_indisponiveis(banco_novo):
    url = make_url(banco_novo.url("rx_api")).set(database="rx_banco_que_nao_existe")
    motor = create_engine(url)
    try:
        with pytest.raises(DadosIndisponiveis):
            RepositorioPostgres(motor).composicoes()
    finally:
        motor.dispose()
