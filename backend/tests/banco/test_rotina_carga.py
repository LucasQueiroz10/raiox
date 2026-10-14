"""Rotina comum das cargas (ADR 0006, seção 5), rodando como rx_ingestao.

Os testes usam a carga da PTAX, de tabela simples, para exercitar a rotina sem depender da fonte.
"""

from datetime import date
from decimal import Decimal

import psycopg
import pytest

from cargas.rotina import (
    CargaEmAndamento,
    ErroDeValidacao,
    expirar_paradas,
    publicar_carga,
    registrar_falha,
    trava,
)


def gravar_ptax(dia: date, falhar: bool = False):
    """Função de gravação de teste: grava uma cotação e, se pedido, recusa depois de gravar."""

    def gravar(conexao: psycopg.Connection, carga_id: int) -> int:
        conexao.execute(
            "INSERT INTO ref.ptax (carga_id, data_cotacao, valor) VALUES (%s, %s, %s)",
            (carga_id, dia, Decimal("5.1234")),
        )
        if falhar:
            raise ErroDeValidacao("cotação fora da faixa esperada")
        return 1

    return gravar


def executar(*comandos: str):
    """Função de gravação de teste que só executa os comandos (para provocar um erro do banco)."""

    def gravar(conexao: psycopg.Connection, carga_id: int) -> int:
        for comando in comandos:
            conexao.execute(comando)
        return 0

    return gravar


def situacao(conexao: psycopg.Connection, carga_id: int) -> tuple:
    return conexao.execute(
        "SELECT status, linhas, motivo_erro FROM ref.carga WHERE carga_id = %s", (carga_id,)
    ).fetchone()


def test_carga_publica_o_que_foi_gravado(banco):
    dia = date(2026, 3, 2)
    with banco.conectar("rx_ingestao") as ingestao, banco.conectar("rx_api") as api:
        carga_id = publicar_carga(ingestao, "ptax", "teste", None, gravar_ptax(dia))

        assert situacao(ingestao, carga_id) == ("publicada", 1, None)
        vigente = api.execute(
            "SELECT valor FROM ref.ptax_vigente WHERE data_cotacao = %s", (dia,)
        ).fetchone()
        assert vigente == (Decimal("5.1234"),)


def test_erro_depois_de_gravar_volta_tudo_e_deixa_a_carga_com_erro(banco):
    dia = date(2026, 3, 3)
    with banco.conectar("rx_ingestao") as ingestao:
        with pytest.raises(ErroDeValidacao):
            publicar_carga(ingestao, "ptax", "teste", None, gravar_ptax(dia, falhar=True))

        carga_id, status, motivo = ingestao.execute(
            "SELECT carga_id, status, motivo_erro FROM ref.carga ORDER BY carga_id DESC LIMIT 1"
        ).fetchone()
        assert status == "com_erro"
        assert motivo == "ErroDeValidacao: cotação fora da faixa esperada"
        gravadas = ingestao.execute(
            "SELECT count(*) FROM ref.ptax WHERE carga_id = %s", (carga_id,)
        ).fetchone()
        assert gravadas == (0,)


def test_falha_antes_de_gravar_fica_registrada_com_erro(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        carga_id = registrar_falha(
            ingestao, "ptax", "teste", None, ConnectionError("portal fora do ar")
        )

        # Exceção de fora do projeto: só o nome da classe (a mensagem pode trazer um valor).
        assert situacao(ingestao, carga_id) == ("com_erro", None, "ConnectionError")


def test_motivo_do_erro_e_cortado_em_500_caracteres(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        carga_id = registrar_falha(ingestao, "ptax", "teste", None, ErroDeValidacao("x" * 2000))

        (motivo,) = ingestao.execute(
            "SELECT motivo_erro FROM ref.carga WHERE carga_id = %s", (carga_id,)
        ).fetchone()
        assert len(motivo) == 500


@pytest.mark.parametrize(
    ("comandos", "esperado"),
    [
        (
            (
                "CREATE TEMP TABLE marcada (x text CONSTRAINT sem_marcador"
                " CHECK (x <> 'ZZMARCADOR')) ON COMMIT DROP",
                "INSERT INTO marcada VALUES ('ZZMARCADOR')",
            ),
            "CheckViolation: sqlstate 23514, restrição sem_marcador, tabela marcada",
        ),
        # Nos erros de dado, até a mensagem principal traz o valor: só o sqlstate.
        (("SELECT 'ZZMARCADOR'::date",), "InvalidDatetimeFormat: sqlstate 22007"),
    ],
)
def test_erro_do_banco_vira_motivo_sem_os_valores_da_linha(banco, comandos, esperado):
    # O texto do erro do psycopg traz o DETAIL com a linha ("Failing row contains ...").
    with banco.conectar("rx_ingestao") as ingestao:
        with pytest.raises(psycopg.Error):
            publicar_carga(ingestao, "ptax", "teste", None, executar(*comandos))

        (motivo,) = ingestao.execute(
            "SELECT motivo_erro FROM ref.carga ORDER BY carga_id DESC LIMIT 1"
        ).fetchone()
        assert motivo == esperado


def test_carga_parada_alem_do_tempo_limite_vira_com_erro(banco_novo):
    with banco_novo.conectar_admin() as admin, banco_novo.conectar("rx_ingestao") as ingestao:
        # Só o administrador consegue escrever a hora de início, para simular a carga parada.
        parada, recente = (
            admin.execute(
                "INSERT INTO ref.carga (tipo, fonte, iniciada_em)"
                " VALUES ('ptax', 'teste', clock_timestamp() - %s::interval) RETURNING carga_id",
                (intervalo,),
            ).fetchone()[0]
            for intervalo in ("4 hours", "10 minutes")
        )

        assert expirar_paradas(ingestao, "ptax") == 1

        status_parada, _, motivo = situacao(ingestao, parada)
        assert (status_parada, motivo) == (
            "com_erro",
            "parada em carregando além do tempo limite",
        )
        assert situacao(ingestao, recente)[0] == "carregando"


def test_so_uma_carga_de_cada_tipo_por_vez(banco):
    with banco.conectar("rx_ingestao") as primeira, banco.conectar("rx_ingestao") as segunda:
        with trava(primeira, "ptax"):
            with pytest.raises(CargaEmAndamento), trava(segunda, "ptax"):
                pass
            with trava(segunda, "composicoes_cvm"):  # outro tipo segue normal
                pass
        with trava(segunda, "ptax"):  # liberada no fim da primeira
            pass
