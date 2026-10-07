"""Conjunto de exemplo sintético usado pela API até o banco existir."""

from decimal import Decimal as D

from app.core.agregacao import agregar
from app.core.composicao import Posicao, TipoItem
from app.core.identificadores import isin_valido
from app.core.lookthrough import abrir_carteira
from app.dados.exemplo import RepositorioExemplo
from app.dados.repositorio import RepositorioDados


def test_implementa_o_repositorio():
    assert isinstance(RepositorioExemplo(), RepositorioDados)


def test_todos_os_isins_sao_validos_e_ficticios():
    repo = RepositorioExemplo()
    isins = set(repo.composicoes()) | set(repo.tabela_classificacao().classificacoes)
    for c in repo.composicoes().values():
        isins |= {i.ativo_id for i in c.itens if i.ativo_id}

    assert isins
    assert all(isin_valido(i) and i.startswith("ZZ") for i in isins)


def test_pesos_de_cada_fundo_nao_passam_de_100_por_cento():
    for c in RepositorioExemplo().composicoes().values():
        assert 0 < sum(i.peso for i in c.itens) <= 1


def test_tem_nome_para_empresas_e_fundos():
    repo = RepositorioExemplo()

    assert all(repo.nome(isin) for isin in repo.composicoes())
    assert all(repo.nome(isin) for isin in repo.tabela_classificacao().classificacoes)
    assert repo.nome("ZZ0000000000") is None


def test_tabela_tem_versao_e_tema_de_ia():
    tabela = RepositorioExemplo().tabela_classificacao()
    temas = {t.tema for c in tabela.classificacoes.values() for t in c.temas}

    assert tabela.versao.startswith("exemplo")
    assert temas == {"Cadeia de IA"}


def test_um_raio_x_com_o_exemplo_expoe_a_cadeia_de_ia():
    repo = RepositorioExemplo()
    fundo_de_fundos = next(i for i in repo.composicoes() if "FOF" in i)

    r = agregar(
        abrir_carteira([Posicao(fundo_de_fundos, D("1000"), TipoItem.FUNDO)], repo.composicoes()),
        repo.tabela_classificacao(),
    )

    assert r.por_tema["Cadeia de IA"].valor > 0
    assert None in r.por_setor  # há uma empresa sem classificação, para exercitar a cobertura
