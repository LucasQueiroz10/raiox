"""Carga da PTAX no banco (cargas/ptax.py; fecha a DT-1), com o Banco Central simulado e
rx_ingestao. Cada teste usa um banco novo: o resultado depende do que já foi publicado."""

from datetime import date
from decimal import Decimal as D

import pytest

from cargas import ptax
from cargas.ptax import TIPO, carregar
from cargas.rotina import ErroDeValidacao

HOJE = date(2026, 10, 14)
SEG, TER, QUA = date(2026, 10, 12), date(2026, 10, 13), HOJE


def banco_central(cotacoes: dict[date, D]):
    """O Banco Central simulado: devolve as cotações pedidas, sem rede."""
    return lambda inicio, fim: {d: v for d, v in cotacoes.items() if inicio <= d <= fim}


def cargas(conexao) -> list[tuple]:
    return conexao.execute(
        "SELECT status, data_referencia, motivo_erro FROM ref.carga WHERE tipo = %s"
        " ORDER BY carga_id",
        (TIPO,),
    ).fetchall()


def vigentes(conexao) -> dict[date, D]:
    return dict(conexao.execute("SELECT data_cotacao, valor FROM ref.ptax_vigente").fetchall())


def test_carga_publica_as_cotacoes_e_a_api_enxerga(banco_novo):
    lidas = {SEG: D("5.1000"), TER: D("5.2000"), QUA: D("5.3000")}
    with banco_novo.conectar("rx_ingestao") as ingestao, banco_novo.conectar("rx_api") as api:
        relatorio = carregar(ingestao, HOJE, banco_central(lidas))

        assert (relatorio.lidas, relatorio.gravadas) == (3, 3)
        assert vigentes(api) == lidas
        assert cargas(ingestao) == [("publicada", QUA, None)]


def test_sem_nada_novo_nenhuma_carga_e_aberta(banco_novo):
    lidas = {SEG: D("5.1000"), TER: D("5.2000")}
    with banco_novo.conectar("rx_ingestao") as ingestao:
        carregar(ingestao, HOJE, banco_central(lidas))

        relatorio = carregar(ingestao, HOJE, banco_central(lidas))

        assert (relatorio.carga_id, relatorio.gravadas) == (None, 0)
        assert len(cargas(ingestao)) == 1


def test_cotacao_nova_e_correcao_do_banco_central_entram_numa_carga_so_com_elas(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao, banco_novo.conectar("rx_api") as api:
        carregar(ingestao, HOJE, banco_central({SEG: D("5.1000"), TER: D("5.2000")}))

        segunda = carregar(
            ingestao,
            HOJE,
            banco_central({SEG: D("5.1000"), TER: D("5.2100"), QUA: D("5.3000")}),
        )

        assert segunda.gravadas == 2  # a terça corrigida e a quarta nova
        (linhas,) = ingestao.execute(
            "SELECT count(*) FROM ref.ptax WHERE carga_id = %s", (segunda.carga_id,)
        ).fetchone()
        assert linhas == 2
        assert vigentes(api) == {SEG: D("5.1000"), TER: D("5.2100"), QUA: D("5.3000")}


def test_variacao_acima_do_limite_fica_com_erro_e_nada_e_publicado(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao:
        carregar(ingestao, HOJE, banco_central({TER: D("5.1000")}))

        with pytest.raises(ErroDeValidacao):
            carregar(ingestao, HOJE, banco_central({TER: D("5.1000"), QUA: D("6.0000")}))

        assert [status for status, _, _ in cargas(ingestao)] == ["publicada", "com_erro"]
        assert vigentes(ingestao) == {TER: D("5.1000")}


def test_banco_central_fora_do_ar_deixa_a_carga_com_erro(banco_novo):
    def fora_do_ar(inicio, fim):
        raise ConnectionError("simulado")

    with banco_novo.conectar("rx_ingestao") as ingestao:
        with pytest.raises(ConnectionError):
            carregar(ingestao, HOJE, fora_do_ar)

        assert cargas(ingestao) == [("com_erro", HOJE, "ConnectionError")]


def test_comando_termina_com_1_e_a_carga_fica_com_erro_sem_rede(banco_novo, monkeypatch):
    def sem_rede(*_args, **_kwargs):
        raise ConnectionError("portal fora do ar ZZMARCADOR")

    monkeypatch.setattr(ptax, "baixar", sem_rede)
    monkeypatch.setenv("RX_BANCO_URL", banco_novo.url("rx_ingestao"))

    assert ptax.main([]) == 1

    with banco_novo.conectar("rx_ingestao") as ingestao:
        ((status, _, motivo),) = cargas(ingestao)
    assert (status, motivo) == ("com_erro", "ConnectionError")
