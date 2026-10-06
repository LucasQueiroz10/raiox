"""N restrito ao negócio atual (v1.1, seção 4): D-09, D-10 e D-20; teste de aceitação 8.

Fixture sintética (tests/fixtures/tenk_v11.html). O que entra no N: Item 1 e, no Item 7, só a
subseção "Results of Operations", sem frases prospectivas e sem o bloco de safe harbor.
"""

import json
from pathlib import Path

import pytest

from ingest.narrativa import (
    contagens_narrativa,
    extrair_texto,
    prospectiva,
    secoes_10k,
    sem_safe_harbor,
    subsecao_resultados,
)

FIX = Path(__file__).resolve().parents[1] / "fixtures"
CONFIG_IRRAE = Path(__file__).resolve().parents[2] / "irrae" / "config"
HTML = (FIX / "tenk_v11.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dicionario():
    return json.loads((CONFIG_IRRAE / "dicionario_narrativa.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def filtro():
    return json.loads((CONFIG_IRRAE / "narrativa_filtro.json").read_text(encoding="utf-8"))


def test_marcadores_prospectivos_vem_da_configuracao(filtro):
    # D-20: lista aprovada provisoriamente; fica na configuração, nunca no código.
    assert filtro["marcadores_prospectivos"] == [
        "expect",
        "anticipate",
        "plan",
        "intend",
        "believe",
        "may",
        "will",
        "could",
        "aim",
        "seek",
        "forward-looking",
    ]


def test_frase_prospectiva_pela_palavra_inteira(filtro):
    marcadores = filtro["marcadores_prospectivos"]

    assert prospectiva("We expect revenue to grow next year.", marcadores)
    assert prospectiva("Demand WILL continue to increase.", marcadores)
    assert not prospectiva("Goodwill increased after the acquisition.", marcadores)
    assert not prospectiva("Cloud revenue grew in the period.", marcadores)
    assert prospectiva("Ignorar", ["ignorar"])  # usa a lista que recebe, não uma fixa


def test_results_of_operations_vai_do_titulo_ate_a_proxima_secao_irma(filtro):
    item7 = secoes_10k(extrair_texto(HTML))["7"]

    texto = subsecao_resultados(item7, filtro["titulos_que_encerram_resultados"])

    assert "Cloud revenue grew" in texto
    assert "Net Sales" in texto  # subtítulo dentro da subseção não a encerra
    assert "Our strategy" not in texto  # visão geral do MD&A fica de fora
    assert "Capital expenditures" not in texto  # Liquidity and Capital Resources encerra


def test_item_7_sem_results_of_operations_nao_contribui(filtro):
    assert subsecao_resultados("Item 7. MD&A\nOverview\nRevenue grew.", ["liquidity"]) == ""


def test_safe_harbor_sai_ate_o_proximo_titulo():
    item1 = secoes_10k(extrair_texto(HTML))["1"]

    texto = sem_safe_harbor(item1)

    assert "This report contains statements" not in texto
    assert "Forward-Looking" not in texto
    assert "Our cloud segment" in texto


def test_contagem_do_n_so_com_negocio_atual(dicionario, filtro):
    # Ficam 3 frases: nuvem (Item 1), aceleradores + modelos (Item 1) e nuvem (Results).
    # Saem: safe harbor, 2 prospectivas, Item 1A, visão geral do MD&A, Liquidity e Item 7A.
    contagens, total = contagens_narrativa(HTML, dicionario["folhas"], filtro)

    assert total == 3
    assert contagens == {
        "ia.nuvem_dc": pytest.approx(2.0),
        "ia.semicondutores": pytest.approx(0.5),
        "ia.modelos_software": pytest.approx(0.5),
    }


def test_frase_do_item_1a_e_prospectiva_nao_entram_no_n(dicionario, filtro):
    # Teste de aceitação 8.
    so_risco_e_futuro = (
        "<p>Item 1. Business</p><p>We plan to build AI data centers in new regions.</p>"
        "<p>Item 1A. Risk Factors</p><p>AI data centers could fail and harm our business.</p>"
    )

    contagens, total = contagens_narrativa(so_risco_e_futuro, dicionario["folhas"], filtro)

    assert (contagens, total) == ({}, 0)
