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


def test_ativos_sao_isins_validos_e_ficticios_e_empresas_tem_prefixo_ficticio():
    repo = RepositorioExemplo()
    ativos = set(repo.composicoes()) | set(repo.empresa_do_ativo())
    for c in repo.composicoes().values():
        ativos |= {i.ativo_id for i in c.itens if i.ativo_id}
    empresas = set(repo.tabela_classificacao().classificacoes) | set(
        repo.empresa_do_ativo().values()
    )

    assert ativos and empresas
    assert all(isin_valido(a) and a.startswith("ZZ") for a in ativos)
    assert all(e.startswith("ZZ:") for e in empresas)


def test_toda_acao_dos_fundos_aponta_para_uma_empresa_com_nome():
    repo = RepositorioExemplo()
    ligacao = repo.empresa_do_ativo()
    acoes = {
        i.ativo_id for c in repo.composicoes().values() for i in c.itens if i.tipo is TipoItem.ACAO
    }

    assert acoes <= set(ligacao)
    assert all(repo.nome(e) for e in ligacao.values())


def test_tem_uma_empresa_com_duas_classes_de_acao():
    ligacao = RepositorioExemplo().empresa_do_ativo()
    classes = {}
    for ativo, empresa in ligacao.items():
        classes.setdefault(empresa, []).append(ativo)

    assert any(len(a) == 2 for a in classes.values())


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
        abrir_carteira(
            [Posicao(fundo_de_fundos, D("1000"), TipoItem.FUNDO)],
            repo.composicoes(),
            empresa_do_ativo=repo.empresa_do_ativo(),
        ),
        repo.tabela_classificacao(),
    )

    assert r.por_tema["Cadeia de IA"].valor > 0
    assert None in r.por_setor  # há uma empresa sem classificação, para exercitar a cobertura
