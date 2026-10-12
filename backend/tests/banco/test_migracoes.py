"""Migrações, usuários e permissões básicas do banco (ADR 0006, seções 2, 6 e 8)."""

import psycopg
import pytest
from alembic.script import ScriptDirectory
from psycopg import sql

from banco.preparar import criar_papeis, url_libpq
from tests.banco.apoio import BancoDeTeste, config_alembic

PAPEIS = ("rx_dono", "rx_api", "rx_ingestao")
SEM_DONO = ("rx_api", "rx_ingestao")


def _scripts() -> ScriptDirectory:
    return ScriptDirectory.from_config(config_alembic())


def _consultar(banco: BancoDeTeste, consulta: str, *parametros: object) -> list[tuple]:
    with banco.conectar_admin() as admin:
        return admin.execute(consulta, parametros).fetchall()


def _pode(banco: BancoDeTeste, funcao: str, papel: str, objeto: str, privilegio: str) -> bool:
    consulta = sql.SQL("SELECT {}(%s, %s, %s)").format(sql.Identifier(funcao))
    with banco.conectar_admin() as admin:
        return admin.execute(consulta, (papel, objeto, privilegio)).fetchone()[0]


# --- Estrutura das migrações (sem banco) ---


def test_migracoes_tem_uma_cabeca_so():
    assert len(_scripts().get_heads()) == 1


def test_migracoes_so_vao_para_frente():
    for revisao in _scripts().walk_revisions():
        with pytest.raises(NotImplementedError):
            revisao.module.downgrade()


# --- Aplicação das migrações ---


def test_migra_do_banco_vazio_ate_a_ultima_versao(banco):
    versoes = _consultar(banco, "SELECT version_num FROM app.alembic_version")

    assert versoes == [(_scripts().get_current_head(),)]


def test_migrar_de_novo_nao_muda_nada(banco):
    banco.migrar("rx_dono")

    versoes = _consultar(banco, "SELECT version_num FROM app.alembic_version")
    assert versoes == [(_scripts().get_current_head(),)]


@pytest.mark.parametrize("usuario", ["rx_api", "rx_ingestao", "admin"])
def test_so_o_rx_dono_aplica_migracoes(banco, usuario):
    usuario = banco.admin if usuario == "admin" else usuario

    with pytest.raises(RuntimeError, match="rx_dono"):
        banco.migrar(usuario)


# --- Usuários ---


def test_preparar_os_papeis_de_novo_nao_falha(banco):
    with psycopg.connect(url_libpq(banco.url_admin), autocommit=True) as admin:
        criar_papeis(admin)


def test_papeis_entram_mas_sem_poderes_especiais(banco):
    linhas = _consultar(
        banco,
        "SELECT rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolreplication,"
        " rolbypassrls FROM pg_roles WHERE rolname = ANY(%s) ORDER BY rolname",
        list(PAPEIS),
    )

    assert linhas == [(p, True, False, False, False, False, False) for p in sorted(PAPEIS)]


# --- Permissões ---


def test_esquema_public_sem_uso_e_sem_permissao(banco):
    for papel in ("public", *SEM_DONO):
        for privilegio in ("USAGE", "CREATE"):
            assert not _pode(banco, "has_schema_privilege", papel, "public", privilegio)

    objetos = _consultar(
        banco,
        "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace"
        " WHERE n.nspname = 'public'",
    )
    assert objetos == [(0,)]


def test_so_os_usuarios_do_projeto_conectam(banco):
    assert not _pode(banco, "has_database_privilege", "public", banco.nome, "CONNECT")
    assert not _pode(banco, "has_database_privilege", "public", banco.nome, "TEMPORARY")
    assert _pode(banco, "has_database_privilege", "rx_api", banco.nome, "CONNECT")
    assert _pode(banco, "has_database_privilege", "rx_ingestao", banco.nome, "CONNECT")


def test_so_a_ingestao_cria_tabela_temporaria(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        ingestao.execute("CREATE TEMP TABLE preparacao (x integer)")

    with banco.conectar("rx_api") as api, pytest.raises(psycopg.errors.InsufficientPrivilege):
        api.execute("CREATE TEMP TABLE preparacao (x integer)")


def test_so_o_dono_cria_objetos(banco):
    for papel in SEM_DONO:
        assert not _pode(banco, "has_database_privilege", papel, banco.nome, "CREATE")
        for esquema in ("ref", "app"):
            assert not _pode(banco, "has_schema_privilege", papel, esquema, "CREATE")

    with banco.conectar("rx_api") as api, pytest.raises(psycopg.errors.InsufficientPrivilege):
        api.execute("CREATE TABLE ref.intrusa (x integer)")


def test_api_e_ingestao_enxergam_o_esquema_ref(banco):
    for papel in SEM_DONO:
        assert _pode(banco, "has_schema_privilege", papel, "ref", "USAGE")


def test_ninguem_alem_do_dono_mexe_na_versao_das_migracoes(banco):
    for papel in ("public", *SEM_DONO):
        for privilegio in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            assert not _pode(banco, "has_table_privilege", papel, "app.alembic_version", privilegio)


def test_tudo_pertence_ao_rx_dono(banco):
    donos_esquemas = _consultar(
        banco,
        "SELECT nspname, pg_get_userbyid(nspowner) FROM pg_namespace"
        " WHERE nspname IN ('ref', 'app') ORDER BY nspname",
    )
    assert donos_esquemas == [("app", "rx_dono"), ("ref", "rx_dono")]

    outros_donos = _consultar(
        banco,
        "SELECT n.nspname, c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace"
        " WHERE n.nspname IN ('ref', 'app') AND pg_get_userbyid(c.relowner) <> 'rx_dono'"
        " UNION ALL"
        " SELECT n.nspname, p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace"
        " WHERE n.nspname IN ('ref', 'app') AND pg_get_userbyid(p.proowner) <> 'rx_dono'",
    )
    assert outros_donos == []


def test_sessoes_em_utc(banco):
    with banco.conectar("rx_api") as api:
        assert api.execute("SELECT current_setting('TimeZone')").fetchone() == ("UTC",)


def test_funcao_nova_nao_fica_aberta_para_todos(banco):
    with banco.conectar("rx_dono") as dono, dono.transaction(force_rollback=True):
        dono.execute(
            "CREATE FUNCTION ref.funcao_de_teste() RETURNS integer LANGUAGE sql AS 'SELECT 1'"
        )
        pode = dono.execute(
            "SELECT has_function_privilege('public', 'ref.funcao_de_teste()', 'EXECUTE')"
        ).fetchone()

    assert pode == (False,)


def test_nenhuma_coluna_em_ponto_flutuante(banco):
    colunas = _consultar(
        banco,
        "SELECT table_schema, table_name, column_name FROM information_schema.columns"
        " WHERE table_schema IN ('ref', 'app') AND data_type IN ('real', 'double precision')",
    )

    assert colunas == []
