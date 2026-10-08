"""Esquema ref: cargas, dados vigentes, formatos do ADR 0005 e permissões (ADR 0006).

Todos os testes usam o mesmo banco, então cada um usa os próprios identificadores sintéticos.
"""

from datetime import date
from decimal import Decimal

import psycopg
import pytest
from psycopg import sql

from tests.banco.apoio import BancoDeTeste, abrir_carga, inserir_composicao, publicar
from tests.ficticios import isin

TABELAS = (
    "carga",
    "composicao",
    "composicao_item",
    "empresa",
    "empresa_apelido",
    "ativo",
    "classificacao",
    "classificacao_tema",
    "ptax",
)
TABELAS_DE_DADOS = TABELAS[1:]
VISOES = (
    "carga_publicada",
    "composicao_vigente",
    "composicao_item_vigente",
    "empresa_vigente",
    "empresa_apelido_vigente",
    "ativo_vigente",
    "classificacao_vigente",
    "classificacao_tema_vigente",
    "ptax_vigente",
)


def _fundo(n: int) -> str:
    """CNPJ sintético de fundo, com dígitos verificadores errados de propósito."""
    return f"CNPJ:9999999900{n:02d}00"


def _pode(banco: BancoDeTeste, funcao: str, *argumentos: str) -> bool:
    marcas = sql.SQL(", ").join(sql.Placeholder() * len(argumentos))
    consulta = sql.SQL("SELECT {}({})").format(sql.Identifier(funcao), marcas)
    with banco.conectar_admin() as admin:
        return admin.execute(consulta, argumentos).fetchone()[0]


# --- Permissões ---


def test_api_le_so_as_visoes(banco):
    for tabela in TABELAS:
        assert not _pode(banco, "has_table_privilege", "rx_api", f"ref.{tabela}", "SELECT")
    for visao in VISOES:
        assert _pode(banco, "has_table_privilege", "rx_api", f"ref.{visao}", "SELECT")
    for objeto in TABELAS + VISOES:
        for privilegio in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            assert not _pode(banco, "has_table_privilege", "rx_api", f"ref.{objeto}", privilegio)


def test_api_nao_le_tabelas_nem_grava(banco):
    with banco.conectar("rx_api") as api:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            api.execute("SELECT * FROM ref.carga")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            api.execute("INSERT INTO ref.carga (tipo, fonte) VALUES ('ptax', 'x')")


def test_ingestao_le_e_acrescenta_mas_nao_altera_nem_apaga(banco):
    for tabela in TABELAS_DE_DADOS:
        nome = f"ref.{tabela}"
        assert _pode(banco, "has_table_privilege", "rx_ingestao", nome, "SELECT")
        assert _pode(banco, "has_table_privilege", "rx_ingestao", nome, "INSERT")
        for privilegio in ("UPDATE", "DELETE", "TRUNCATE"):
            assert not _pode(banco, "has_table_privilege", "rx_ingestao", nome, privilegio)


def test_ingestao_so_mexe_no_andamento_da_carga(banco):
    colunas = ("carga_id", "tipo", "fonte", "data_referencia", "status", "iniciada_em")
    colunas += ("publicada_em", "linhas", "motivo_erro")
    for coluna in colunas:
        pode_inserir = _pode(
            banco, "has_column_privilege", "rx_ingestao", "ref.carga", coluna, "INSERT"
        )
        pode_mudar = _pode(
            banco, "has_column_privilege", "rx_ingestao", "ref.carga", coluna, "UPDATE"
        )
        assert pode_inserir == (coluna in ("tipo", "fonte", "data_referencia"))
        assert pode_mudar == (coluna in ("status", "linhas", "motivo_erro"))
    for privilegio in ("DELETE", "TRUNCATE"):
        assert not _pode(banco, "has_table_privilege", "rx_ingestao", "ref.carga", privilegio)


# --- Ciclo da carga (seções 3 e 5) ---


def test_carga_nasce_carregando_e_a_publicacao_tem_data_do_banco(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        carga = abrir_carga(ingestao, "ptax")
        antes = ingestao.execute(
            "SELECT status, publicada_em FROM ref.carga WHERE carga_id = %s", (carga,)
        ).fetchone()
        publicar(ingestao, carga, linhas=3)
        depois = ingestao.execute(
            "SELECT status, publicada_em IS NOT NULL, linhas FROM ref.carga WHERE carga_id = %s",
            (carga,),
        ).fetchone()

    assert antes == ("carregando", None)
    assert depois == ("publicada", True, 3)


def test_ingestao_nao_abre_carga_ja_publicada_nem_escolhe_a_data(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            ingestao.execute(
                "INSERT INTO ref.carga (tipo, fonte, status) VALUES ('ptax', 'x', 'publicada')"
            )
        carga = abrir_carga(ingestao, "ptax")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            ingestao.execute(
                "UPDATE ref.carga SET publicada_em = '2000-01-01' WHERE carga_id = %s", (carga,)
            )


@pytest.mark.parametrize("novo_status", ["carregando", "com_erro", "publicada"])
def test_carga_publicada_nao_volta_atras(banco, novo_status):
    with banco.conectar("rx_ingestao") as ingestao:
        carga = abrir_carga(ingestao, "ptax")
        publicar(ingestao, carga)
        with pytest.raises(psycopg.errors.RaiseException):
            ingestao.execute(
                "UPDATE ref.carga SET status = %s, motivo_erro = %s WHERE carga_id = %s",
                (novo_status, "teste" if novo_status == "com_erro" else None, carga),
            )


def test_carga_com_erro_guarda_o_motivo_e_nao_reabre(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        carga = abrir_carga(ingestao, "ptax")
        with pytest.raises(psycopg.errors.CheckViolation):
            ingestao.execute(
                "UPDATE ref.carga SET status = 'com_erro' WHERE carga_id = %s", (carga,)
            )
        ingestao.execute(
            "UPDATE ref.carga SET status = 'com_erro', motivo_erro = 'soma dos pesos'"
            " WHERE carga_id = %s",
            (carga,),
        )
        with pytest.raises(psycopg.errors.RaiseException):
            publicar(ingestao, carga)


def test_linha_nao_entra_em_carga_encerrada(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        ptax = abrir_carga(ingestao, "ptax")
        publicar(ingestao, ptax)
        with pytest.raises(psycopg.errors.RaiseException):
            ingestao.execute(
                "INSERT INTO ref.ptax (carga_id, data_cotacao, valor) VALUES (%s, %s, 5)",
                (ptax, date(2001, 1, 2)),
            )

        cvm = abrir_carga(ingestao, "composicoes_cvm", date(2026, 8, 31))
        composicao = inserir_composicao(
            ingestao, cvm, _fundo(1), date(2026, 8, 31), [(isin("A1"), "1", "acao")]
        )
        publicar(ingestao, cvm)
        with pytest.raises(psycopg.errors.RaiseException):
            inserir_composicao(ingestao, cvm, _fundo(2), date(2026, 8, 31), [])
        with pytest.raises(psycopg.errors.RaiseException):
            ingestao.execute(
                "INSERT INTO ref.composicao_item (composicao_id, ordem, ativo_id, tipo, peso)"
                " VALUES (%s, 2, %s, 'acao', 0)",
                (composicao, isin("A2")),
            )


def test_linha_so_entra_em_carga_do_seu_tipo(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        ptax = abrir_carga(ingestao, "ptax")
        with pytest.raises(psycopg.errors.RaiseException):
            inserir_composicao(ingestao, ptax, _fundo(3), date(2026, 8, 31), [])


def test_ingestao_nao_altera_nem_apaga_linha_gravada(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            ingestao.execute("UPDATE ref.ptax SET valor = 1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            ingestao.execute("DELETE FROM ref.composicao_item")


# --- O que a API vê (seção 3) ---


def test_api_ve_composicao_so_depois_de_publicada(banco):
    fundo = _fundo(10)
    with banco.conectar("rx_ingestao") as ingestao, banco.conectar("rx_api") as api:
        carga = abrir_carga(ingestao, "composicoes_cvm", date(2026, 8, 31))
        inserir_composicao(
            ingestao,
            carga,
            fundo,
            date(2026, 8, 31),
            [(isin("B1"), "0.6", "acao"), (None, "0.4", "caixa")],
        )
        consulta = "SELECT fundo_id FROM ref.composicao_vigente WHERE fundo_id = %s"
        antes = api.execute(consulta, (fundo,)).fetchall()
        publicar(ingestao, carga)
        depois = api.execute(consulta, (fundo,)).fetchall()
        itens = api.execute(
            "SELECT ordem, ativo_id, tipo, peso FROM ref.composicao_item_vigente"
            " WHERE fundo_id = %s ORDER BY ordem",
            (fundo,),
        ).fetchall()

    assert antes == []
    assert depois == [(fundo,)]
    assert itens == [(1, isin("B1"), "acao", Decimal("0.6")), (2, None, "caixa", Decimal("0.4"))]


def test_composicao_vigente_e_a_do_mes_mais_recente(banco):
    fundo = _fundo(11)
    with banco.conectar("rx_ingestao") as ingestao:
        for dia, publica in [
            (date(2026, 7, 31), True),
            (date(2026, 8, 31), True),
            (date(2026, 6, 30), True),  # mês antigo publicado depois não volta a valer
            (date(2026, 9, 30), False),  # ainda carregando
        ]:
            carga = abrir_carga(ingestao, "composicoes_cvm", dia)
            inserir_composicao(ingestao, carga, fundo, dia, [(isin("C1"), "1", "acao")])
            if publica:
                publicar(ingestao, carga)
        erro = abrir_carga(ingestao, "composicoes_cvm", date(2026, 10, 31))
        inserir_composicao(ingestao, erro, fundo, date(2026, 10, 31), [])
        ingestao.execute(
            "UPDATE ref.carga SET status = 'com_erro', motivo_erro = 'teste' WHERE carga_id = %s",
            (erro,),
        )

    with banco.conectar("rx_api") as api:
        vigentes = api.execute(
            "SELECT data_referencia FROM ref.composicao_vigente WHERE fundo_id = %s", (fundo,)
        ).fetchall()

    assert vigentes == [(date(2026, 8, 31),)]


def test_no_mesmo_mes_vale_a_publicada_por_ultimo(banco):
    fundo = _fundo(12)
    with banco.conectar("rx_ingestao") as ingestao:
        for dia, ativo in [(date(2026, 8, 31), isin("D1")), (date(2026, 8, 28), isin("D2"))]:
            carga = abrir_carga(ingestao, "composicoes_cvm", dia)
            inserir_composicao(ingestao, carga, fundo, dia, [(ativo, "1", "acao")])
            publicar(ingestao, carga)

    with banco.conectar("rx_api") as api:
        itens = api.execute(
            "SELECT ativo_id FROM ref.composicao_item_vigente WHERE fundo_id = %s", (fundo,)
        ).fetchall()

    assert itens == [(isin("D2"),)]


def test_pesos_voltam_exatos_como_decimal(banco):
    fundo = _fundo(13)
    peso = "0.1234567890123456789012345678901234567890123456789"
    with banco.conectar("rx_ingestao") as ingestao:
        carga = abrir_carga(ingestao, "composicoes_cvm", date(2026, 8, 31))
        inserir_composicao(ingestao, carga, fundo, date(2026, 8, 31), [(isin("E1"), peso, "acao")])
        publicar(ingestao, carga)

    with banco.conectar("rx_api") as api:
        lido = api.execute(
            "SELECT peso FROM ref.composicao_item_vigente WHERE fundo_id = %s", (fundo,)
        ).fetchone()[0]

    assert isinstance(lido, Decimal)
    assert lido == Decimal(peso)


def _publicar_identificacao(ingestao: psycopg.Connection, empresa: str, publica: bool) -> None:
    carga = abrir_carga(ingestao, "identificacao")
    ingestao.execute(
        "INSERT INTO ref.empresa (carga_id, empresa_id, nome) VALUES (%s, %s, %s)",
        (carga, empresa, "Empresa Sintética"),
    )
    ingestao.execute(
        "INSERT INTO ref.ativo (carga_id, ativo_id, tipo, empresa_id, nome)"
        " VALUES (%s, %s, 'acao', %s, %s)",
        (carga, isin(empresa), empresa, "Classe Sintética"),
    )
    if publica:
        publicar(ingestao, carga)


def test_identificacao_vigente_e_a_ultima_foto_publicada(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        _publicar_identificacao(ingestao, "ZZ:VELHA", publica=True)
        _publicar_identificacao(ingestao, "ZZ:NOVA", publica=True)
        _publicar_identificacao(ingestao, "ZZ:RASCUNHO", publica=False)

    with banco.conectar("rx_api") as api:
        empresas = {
            e for (e,) in api.execute("SELECT empresa_id FROM ref.empresa_vigente").fetchall()
        }
        ativos = api.execute("SELECT ativo_id, empresa_id FROM ref.ativo_vigente").fetchall()

    assert empresas == {"ZZ:NOVA"}
    assert ativos == [(isin("ZZ:NOVA"), "ZZ:NOVA")]


def test_classificacao_vigente_mostra_so_linhas_aprovadas(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        carga = abrir_carga(ingestao, "classificacao")
        for empresa, origem, status in [
            ("ZZ:APROVADA", "oficial", "aprovado"),
            ("ZZ:PRELIMINAR", "ia", "rascunho"),
        ]:
            ingestao.execute(
                "INSERT INTO ref.classificacao"
                " (carga_id, empresa_id, setor, setor_origem, setor_status)"
                " VALUES (%s, %s, 'Tecnologia', %s, %s)",
                (carga, empresa, origem, status),
            )
        for subtema, origem, status in [
            ("Nuvem", "manual", "aprovado"),
            ("Chips", "ia", "rascunho"),
        ]:
            ingestao.execute(
                "INSERT INTO ref.classificacao_tema"
                " (carga_id, empresa_id, tema, subtema, peso, origem, status)"
                " VALUES (%s, 'ZZ:APROVADA', 'Cadeia de IA', %s, 0.25, %s, %s)",
                (carga, subtema, origem, status),
            )
        publicar(ingestao, carga)

    with banco.conectar("rx_api") as api:
        setores = api.execute(
            "SELECT empresa_id, setor FROM ref.classificacao_vigente ORDER BY empresa_id"
        ).fetchall()
        temas = api.execute(
            "SELECT empresa_id, subtema, peso FROM ref.classificacao_tema_vigente"
        ).fetchall()

    assert setores == [("ZZ:APROVADA", "Tecnologia")]
    assert temas == [("ZZ:APROVADA", "Nuvem", Decimal("0.25"))]


def test_ptax_vigente_usa_a_correcao_mais_recente(banco):
    dias = (date(2001, 1, 2), date(2001, 1, 3))
    with banco.conectar("rx_ingestao") as ingestao:
        for linhas in ([(dias[0], "5.1"), (dias[1], "5.2")], [(dias[1], "5.25")]):
            carga = abrir_carga(ingestao, "ptax")
            for dia, valor in linhas:
                ingestao.execute(
                    "INSERT INTO ref.ptax (carga_id, data_cotacao, valor) VALUES (%s, %s, %s)",
                    (carga, dia, Decimal(valor)),
                )
            publicar(ingestao, carga)

    with banco.conectar("rx_api") as api:
        cotacoes = api.execute(
            "SELECT data_cotacao, valor FROM ref.ptax_vigente"
            " WHERE data_cotacao = ANY(%s) ORDER BY data_cotacao",
            (list(dias),),
        ).fetchall()

    assert cotacoes == [(dias[0], Decimal("5.1")), (dias[1], Decimal("5.25"))]


def test_carga_publicada_lista_so_as_publicadas(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        publicada = abrir_carga(ingestao, "ptax")
        publicar(ingestao, publicada)
        carregando = abrir_carga(ingestao, "ptax")

    with banco.conectar("rx_api") as api:
        cargas = {c for (c,) in api.execute("SELECT carga_id FROM ref.carga_publicada")}

    assert publicada in cargas
    assert carregando not in cargas


# --- Formatos do ADR 0005 ---


@pytest.mark.parametrize(
    "valor", [isin("F1"), "BRZZZZZZZZZ1", "IEZZZZZZZZZ1", "US:ZZETF", "US:ZZA.B", _fundo(20)]
)
def test_ativo_id_aceita_os_formatos_do_adr_0005(banco, valor):
    with banco.conectar_admin() as admin:
        assert admin.execute("SELECT %s::ref.ativo_id", (valor,)).fetchone() == (valor,)


@pytest.mark.parametrize(
    "valor",
    [
        "USZZZZZZZZZ1",  # ISIN americano
        "CAZZZZZZZZZ1",  # ISIN de país fora da lista permitida
        "ZZZZZZZZ1",  # formato de CUSIP
        "ZZZZZZ1",  # formato de SEDOL
        "US:ZZZZZZZZ1",  # CUSIP no lugar do ticker
        "CNPJ:123",
        "zzchips00019",
    ],
)
def test_ativo_id_recusa_identificador_fora_do_adr_0005(banco, valor):
    with banco.conectar_admin() as admin, pytest.raises(psycopg.errors.CheckViolation):
        admin.execute("SELECT %s::ref.ativo_id", (valor,))


@pytest.mark.parametrize(
    "valor",
    ["ZZ:CHIPS", "BR:CNPJ:99999999000100", "US:CIK:9999999999", "LEI:ZZZZZZZZZZZZZZZZZZ00"],
)
def test_empresa_id_aceita_os_formatos_do_adr_0005(banco, valor):
    with banco.conectar_admin() as admin:
        assert admin.execute("SELECT %s::ref.empresa_id", (valor,)).fetchone() == (valor,)


@pytest.mark.parametrize(
    "valor", ["BR:CNPJ:123", "US:CIK:123", "LEI:zzz", "ZZCHIPS", "US:ZZETF", isin("G1")]
)
def test_empresa_id_recusa_outros_formatos(banco, valor):
    with banco.conectar_admin() as admin, pytest.raises(psycopg.errors.CheckViolation):
        admin.execute("SELECT %s::ref.empresa_id", (valor,))


def test_colunas_de_identificador_usam_os_formatos_do_adr_0005(banco):
    esperado = {
        "ativo_id": "ativo_id",
        "fundo_id": "ativo_id",
        "ativo_objeto": "ativo_id",
        "aproximado_por": "ativo_id",
        "isin": "isin_permitido",
        "empresa_id": "empresa_id",
        "emissor": "empresa_id",
        "apelido": "empresa_id",
    }
    with banco.conectar_admin() as admin:
        colunas = admin.execute(
            "SELECT table_name, column_name, domain_name FROM information_schema.columns"
            " WHERE table_schema = 'ref' AND column_name = ANY(%s) AND table_name = ANY(%s)",
            (list(esperado), list(TABELAS)),
        ).fetchall()

    assert colunas
    for tabela, coluna, dominio in colunas:
        assert dominio == esperado[coluna], (tabela, coluna)
