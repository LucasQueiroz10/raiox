"""Carga da PTAX (cargas/ptax.py), sem banco: o que gravar, a trava de variação e a leitura da
resposta do Banco Central. Cotações sintéticas."""

import json
from datetime import date
from decimal import Decimal as D

import pytest

from cargas import ptax
from cargas.ptax import a_gravar, baixar_cotacoes, conferir_variacao
from cargas.rotina import ErroDeValidacao

SEG, TER, QUA = date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)


def test_grava_as_datas_novas_e_as_corrigidas_e_pula_as_iguais():
    publicadas = {SEG: D("5.1000"), TER: D("5.2000")}
    lidas = {SEG: D("5.1000"), TER: D("5.2100"), QUA: D("5.3000")}

    assert a_gravar(lidas, publicadas) == {TER: D("5.2100"), QUA: D("5.3000")}


def test_variacao_dentro_do_limite_passa():
    conferir_variacao({QUA: D("5.6000")}, {TER: D("5.1000")})  # +9,8%


def test_variacao_acima_de_10_por_cento_trava_e_diz_a_data():
    with pytest.raises(ErroDeValidacao, match="14/10/2026") as erro:
        conferir_variacao({QUA: D("5.7000")}, {TER: D("5.1000")})  # +11,8%

    assert "5.7" not in str(erro.value)  # a mensagem diz a data e a variação, não o valor


def test_correcao_de_uma_data_antiga_tambem_confere_o_dia_seguinte():
    # O BCB corrige a terça; a quarta, já publicada, passa a variar demais sobre ela.
    publicadas = {SEG: D("5.1000"), TER: D("5.1000"), QUA: D("5.1000")}

    with pytest.raises(ErroDeValidacao, match="14/10/2026"):
        conferir_variacao({TER: D("4.6000")}, publicadas)


def test_na_primeira_carga_confere_a_variacao_entre_as_datas_lidas():
    with pytest.raises(ErroDeValidacao):
        conferir_variacao({SEG: D("5.0000"), TER: D("6.0000")}, {})


def resposta(*linhas: tuple[str, str]) -> bytes:
    return json.dumps(
        {
            "value": [
                {"cotacaoVenda": float(v), "dataHoraCotacao": f"{d} 13:09:29.000"}
                for d, v in linhas
            ]
        }
    ).encode()


def test_le_a_resposta_do_banco_central(monkeypatch):
    monkeypatch.setattr(
        ptax,
        "baixar",
        lambda url, permitido: resposta(
            ("2026-10-13", "5.2"),
        ),
    )

    assert baixar_cotacoes(SEG, QUA) == {TER: D("5.2")}


@pytest.mark.parametrize(
    "conteudo",
    [b"<html>fora do ar</html>", b"[]", resposta(), json.dumps({"value": [{"x": 1}]}).encode()],
    ids=["nao_e_json", "lista", "sem_cotacoes", "linha_sem_cotacao"],
)
def test_resposta_fora_do_formato_ou_vazia_e_erro_de_validacao(monkeypatch, conteudo):
    monkeypatch.setattr(ptax, "baixar", lambda url, permitido: conteudo)

    with pytest.raises(ErroDeValidacao):
        baixar_cotacoes(SEG, QUA)


def test_baixa_so_do_endereco_da_api_ptax(monkeypatch):
    pedidos = []

    def baixar(url, permitido):
        pedidos.append((url, permitido))
        return resposta(("2026-10-13", "5.2"))

    monkeypatch.setattr(ptax, "baixar", baixar)
    baixar_cotacoes(SEG, QUA)

    ((url, permitido),) = pedidos
    assert permitido == "https://olinda.bcb.gov.br/olinda/servico/PTAX/"
    assert url.startswith(permitido)
