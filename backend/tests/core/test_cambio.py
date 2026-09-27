"""Cotações inventadas, no formato da API PTAX (Olinda) do Banco Central."""

from datetime import date
from decimal import Decimal as D

import pytest

from app.core.cambio import escolher_ptax, ler_ptax_olinda


def resposta(*linhas: dict) -> dict:
    return {"@odata.context": "teste", "value": list(linhas)}


def linha(venda: float, quando: str, boletim: str | None = None) -> dict:
    d = {"cotacaoCompra": venda - 0.01, "cotacaoVenda": venda, "dataHoraCotacao": quando}
    if boletim:
        d["tipoBoletim"] = boletim
    return d


def test_le_a_cotacao_de_venda_por_data():
    r = resposta(
        linha(5.1234, "2026-09-24 13:04:20.123"),
        linha(5.2345, "2026-09-25 13:10:02.456"),
    )

    assert ler_ptax_olinda(r) == {date(2026, 9, 24): D("5.1234"), date(2026, 9, 25): D("5.2345")}


def test_usa_so_o_boletim_de_fechamento_quando_ha_varios():
    r = resposta(
        linha(5.0, "2026-09-24 10:00:00.0", "Abertura"),
        linha(5.1, "2026-09-24 11:00:00.0", "Intermediário"),
        linha(5.3, "2026-09-24 13:00:00.0", "Fechamento"),
    )

    assert ler_ptax_olinda(r) == {date(2026, 9, 24): D("5.3")}


def test_valor_decimal_nao_herda_erro_de_float():
    r = resposta(linha(5.1234, "2026-09-24 13:00:00.0"))

    assert ler_ptax_olinda(r)[date(2026, 9, 24)] == D("5.1234")


def test_resposta_vazia():
    assert ler_ptax_olinda(resposta()) == {}


@pytest.mark.parametrize(
    "invalida",
    [
        {"cotacaoVenda": 0, "dataHoraCotacao": "2026-09-24 13:00:00.0"},
        {"cotacaoVenda": -5.1, "dataHoraCotacao": "2026-09-24 13:00:00.0"},
        {"dataHoraCotacao": "2026-09-24 13:00:00.0"},
    ],
)
def test_recusa_cotacao_invalida(invalida):
    with pytest.raises(ValueError):
        ler_ptax_olinda(resposta(invalida))


# Cotações inventadas: 04/09 (sex), 08/09 (ter), 23/12 (qua), 25/09 (sex) de 2026.
COTACOES = {
    date(2026, 9, 4): D("5.40"),
    date(2026, 9, 8): D("5.41"),
    date(2026, 9, 25): D("5.42"),
    date(2026, 12, 23): D("5.43"),
}


def test_dia_util_com_cotacao_usa_a_propria_data():
    p = escolher_ptax(COTACOES, date(2026, 9, 25))

    assert (p.data_cotacao, p.valor, p.data_pedida) == (
        date(2026, 9, 25),
        D("5.42"),
        date(2026, 9, 25),
    )


def test_fim_de_semana_volta_para_a_sexta():
    assert escolher_ptax(COTACOES, date(2026, 9, 27)).data_cotacao == date(2026, 9, 25)


def test_feriado_volta_para_o_dia_util_anterior():
    # 07/09/2026 é segunda-feira e feriado (Independência).
    assert escolher_ptax(COTACOES, date(2026, 9, 7)).data_cotacao == date(2026, 9, 4)


def test_dia_util_sem_cotacao_volta_mais_um_dia_util():
    # 24/12/2026 é quinta e dia útil, mas não há cotação: usa 23/12.
    p = escolher_ptax(COTACOES, date(2026, 12, 24))

    assert (p.data_cotacao, p.data_pedida) == (date(2026, 12, 23), date(2026, 12, 24))


def test_sem_cotacao_nos_ultimos_10_dias_uteis_da_erro():
    with pytest.raises(LookupError):
        escolher_ptax(COTACOES, date(2026, 11, 30))
