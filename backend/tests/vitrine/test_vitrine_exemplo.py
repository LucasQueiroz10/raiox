"""Snapshots de exemplo da vitrine: empresas reais, pesos e exposição inventados (ADR 0009)."""

import json
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from vitrine.exemplo import PASTA_PADRAO, gerar, texto_json
from vitrine.snapshot import Snapshot


def test_gera_as_tres_carteiras_validas_e_marcadas_como_ilustrativas():
    snapshots = gerar()

    assert [s.carteira.id for s in snapshots] == ["big-techs", "sp500", "ibovespa"]
    for snapshot in snapshots:
        Snapshot.model_validate(snapshot.model_dump())
        assert snapshot.ilustrativo is True


def test_e_deterministico():
    assert [texto_json(s) for s in gerar()] == [texto_json(s) for s in gerar()]


def test_big_techs_tem_as_quatro_empresas_com_25_por_cento():
    big_techs = gerar()[0]

    assert [e.ticker for e in big_techs.empresas] == ["NVDA", "AMZN", "AAPL", "MSFT"]
    assert {e.peso_efetivo for e in big_techs.empresas} == {Decimal("0.25")}


def test_exemplos_nao_citam_fonte():
    # Composição e exposição são inventadas: creditar o CDA ou o N-PORT seria falso.
    for snapshot in gerar():
        assert snapshot.fontes_carteira == []
        assert all(e.fontes == [] for e in snapshot.empresas)


def test_exemplos_exercitam_as_tres_origens_do_irrae():
    for snapshot in gerar()[1:]:
        origens = {e.irrae.origem for e in snapshot.empresas}
        assert origens == {"irrae", "so_prior", "nao_coberto"}


def test_sp500_tem_mais_de_20_empresas_para_exercitar_ver_todas():
    assert len(gerar()[1].empresas) > 20


def test_arquivos_commitados_batem_com_o_gerador():
    # Mesma ideia do contrato da API: quem mudar o gerador regenera e commita os arquivos.
    for snapshot in gerar():
        arquivo = PASTA_PADRAO / f"{snapshot.carteira.id}.json"
        assert arquivo.read_text(encoding="utf-8") == texto_json(snapshot), (
            f"{arquivo.name} desatualizado: rode python -m vitrine.exemplo"
        )


@settings(max_examples=25, deadline=None)
@given(semente=st.integers(min_value=0, max_value=10_000))
def test_qualquer_semente_gera_snapshots_que_fecham(semente):
    for snapshot in gerar(semente):
        texto = texto_json(snapshot)
        Snapshot.model_validate(json.loads(texto))
