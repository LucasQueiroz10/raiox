"""Migração 0004: código interno da B3, ticker com número na raiz e o tipo dos FIIs (ADR 0005 e
ADR 0008, etapa 4; decisões de 13/10/2026)."""

import psycopg
import pytest

from tests.banco.apoio import abrir_carga, publicar
from tests.ficticios import cnpj

EMPRESA = f"BR:CNPJ:{cnpj('ID-EMPRESA')}"
FII = f"CNPJ:{cnpj('ID-FII')}"


@pytest.mark.parametrize("valor", ["B3:ZZAA3", "B3:ZZAA11", "B3:Z3ZA3"])
def test_ativo_id_aceita_o_codigo_interno_da_b3(banco, valor):
    with banco.conectar_admin() as admin:
        assert admin.execute("SELECT %s::ref.ativo_id", (valor,)).fetchone() == (valor,)


@pytest.mark.parametrize(
    "valor",
    [
        "B3:zzaa3",  # minúsculas
        "B3:ZZAA",  # sem o número da classe
        "B3:3ZAA3",  # raiz começando por número
        "B3:ZZAA123",  # três dígitos
        "ZZAA3",  # ticker sem o prefixo
    ],
)
def test_ativo_id_recusa_codigo_fora_do_formato(banco, valor):
    with banco.conectar_admin() as admin, pytest.raises(psycopg.errors.CheckViolation):
        admin.execute("SELECT %s::ref.ativo_id", (valor,))


def inserir_ativo(conexao, carga: int, **colunas) -> None:
    nomes = ", ".join(colunas)
    marcas = ", ".join(["%s"] * len(colunas))
    conexao.execute(
        f"INSERT INTO ref.ativo (carga_id, {nomes}) VALUES (%s, {marcas})",  # noqa: S608
        (carga, *colunas.values()),
    )


def carga_com_empresa(ingestao) -> int:
    carga = abrir_carga(ingestao, "identificacao")
    ingestao.execute(
        "INSERT INTO ref.empresa (carga_id, empresa_id, nome) VALUES (%s, %s, 'EMPRESA')",
        (carga, EMPRESA),
    )
    return carga


def test_acao_pelo_codigo_interno_com_ticker_de_raiz_com_numero(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        carga = carga_com_empresa(ingestao)
        inserir_ativo(
            ingestao, carga, ativo_id="B3:Z3ZA3", tipo="acao", empresa_id=EMPRESA, ticker_b3="Z3ZA3"
        )


def test_codigo_interno_da_b3_so_vale_para_acao(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        carga = carga_com_empresa(ingestao)
        with pytest.raises(psycopg.errors.CheckViolation):
            inserir_ativo(ingestao, carga, ativo_id="B3:ZZFF11", tipo="fundo")


@pytest.mark.parametrize(
    ("colunas", "aceita"),
    [
        ({"fii_tipo": "tijolo", "fii_segmento": "Logística"}, True),
        ({"fii_tipo": "tijolo"}, True),  # vários segmentos
        ({"fii_tipo": "papel"}, True),
        ({"fii_tipo": "fundo_de_fundos"}, True),
        ({"fii_tipo": "generico"}, True),
        ({"fii_tipo": "papel", "fii_segmento": "Logística"}, False),  # segmento só no tijolo
        ({"fii_segmento": "Logística"}, False),  # segmento sem tipo
        ({"fii_tipo": "hibrido"}, False),  # tipo fora da lista
    ],
)
def test_tipo_e_segmento_do_fii(banco, colunas, aceita):
    with banco.conectar("rx_ingestao") as ingestao:
        carga = abrir_carga(ingestao, "identificacao")
        if aceita:
            inserir_ativo(ingestao, carga, ativo_id=FII, tipo="fundo", **colunas)
        else:
            with pytest.raises(psycopg.errors.CheckViolation):
                inserir_ativo(ingestao, carga, ativo_id=FII, tipo="fundo", **colunas)


def test_tipo_de_fii_so_vale_para_fundo(banco):
    with banco.conectar("rx_ingestao") as ingestao:
        carga = carga_com_empresa(ingestao)
        with pytest.raises(psycopg.errors.CheckViolation):
            inserir_ativo(
                ingestao,
                carga,
                ativo_id="B3:ZZAA3",
                tipo="acao",
                empresa_id=EMPRESA,
                fii_tipo="tijolo",
            )


def test_api_ve_o_tipo_do_fii_na_identificacao_vigente(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao, banco_novo.conectar("rx_api") as api:
        carga = abrir_carga(ingestao, "identificacao")
        inserir_ativo(
            ingestao, carga, ativo_id=FII, tipo="fundo", fii_tipo="tijolo", fii_segmento="Hotel"
        )
        publicar(ingestao, carga)

        vigente = api.execute(
            "SELECT fii_tipo, fii_segmento FROM ref.ativo_vigente WHERE ativo_id = %s", (FII,)
        ).fetchone()

        assert vigente == ("tijolo", "Hotel")
