"""Amostra de frases do N para revisão manual e cálculo da precisão (D-11). Só dados sintéticos."""

import json
from pathlib import Path

import pytest

from irrae.revisao_narrativa import (
    amostra_estratificada,
    escrever_csv,
    exigir_fora_do_repositorio,
    ler_csv,
    precisao,
    rotular,
)

FIX = Path(__file__).resolve().parents[1] / "fixtures"
CONFIG = Path(__file__).resolve().parents[2] / "irrae" / "config"
REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def dicionario():
    return json.loads((CONFIG / "dicionario_narrativa.json").read_text(encoding="utf-8"))["folhas"]


@pytest.fixture(scope="module")
def filtro():
    return json.loads((CONFIG / "narrativa_filtro.json").read_text(encoding="utf-8"))


def _linhas(rotulo, empresas, n):
    return [
        {"frase": f"{rotulo} {e} {i}", "empresa": e, "item": "1", "rotulo_automatico": rotulo}
        for i in range(n)
        for e in empresas
    ]


def test_rotula_cada_frase_do_n_com_a_folha_ou_nenhuma(dicionario, filtro):
    html = (FIX / "tenk_v11.html").read_text(encoding="utf-8")
    sem_ia = (
        "<p>Item 1. Business</p><p>We operate retail stores and sell consumer goods nationwide.</p>"
    )

    linhas = rotular(html, dicionario, filtro, "ZZ:A")
    nenhuma = rotular(sem_ia, dicionario, filtro, "ZZ:B")

    assert [(r["item"], r["rotulo_automatico"]) for r in linhas] == [
        ("1", "ia.nuvem_dc"),
        ("1", "ia.modelos_software;ia.semicondutores"),
        ("7", "ia.nuvem_dc"),
    ]
    assert all(r["empresa"] == "ZZ:A" for r in linhas)
    assert [r["rotulo_automatico"] for r in nenhuma] == ["nenhuma"]


def test_amostra_divide_igual_entre_rotulos_e_espalha_pelas_empresas():
    linhas = (
        _linhas("ia.nuvem_dc", ["ZZ:A", "ZZ:B"], 50)
        + _linhas("ia.semicondutores", ["ZZ:A"], 5)
        + _linhas("nenhuma", ["ZZ:A", "ZZ:B"], 50)
    )

    amostra = amostra_estratificada(linhas, n=30, semente=1)

    por_rotulo = {}
    for r in amostra:
        por_rotulo.setdefault(r["rotulo_automatico"], []).append(r)
    assert len(amostra) == 30
    assert len(por_rotulo["ia.semicondutores"]) == 5  # tinha só 5: entram todas
    assert sorted(len(v) for k, v in por_rotulo.items() if k != "ia.semicondutores") == [12, 13]
    nuvem = [r["empresa"] for r in por_rotulo["ia.nuvem_dc"]]
    assert abs(nuvem.count("ZZ:A") - nuvem.count("ZZ:B")) <= 1
    assert len({r["frase"] for r in amostra}) == 30  # sem repetir frase


def test_amostra_e_reprodutivel_pela_semente():
    linhas = _linhas("ia.nuvem_dc", ["ZZ:A", "ZZ:B"], 50) + _linhas("nenhuma", ["ZZ:A"], 50)

    a = amostra_estratificada(linhas, n=20, semente=7)
    b = amostra_estratificada(linhas, n=20, semente=7)
    c = amostra_estratificada(linhas, n=20, semente=8)

    assert a == b and a != c


def test_amostra_menor_que_o_pedido_devolve_tudo():
    linhas = _linhas("nenhuma", ["ZZ:A"], 4)

    assert len(amostra_estratificada(linhas, n=200, semente=0)) == 4


def test_csv_tem_coluna_vazia_para_o_rotulo_manual(tmp_path):
    caminho = tmp_path / "amostra.csv"

    escrever_csv(_linhas("ia.nuvem_dc", ["ZZ:A"], 2), caminho)
    lido = ler_csv(caminho)

    assert list(lido[0]) == ["frase", "empresa", "item", "rotulo_automatico", "rotulo_manual"]
    assert all(r["rotulo_manual"] == "" for r in lido)


def test_precisao_so_conta_frases_ja_rotuladas_e_compara_o_conjunto_de_folhas():
    rotuladas = [
        {"rotulo_automatico": "ia.nuvem_dc", "rotulo_manual": "ia.nuvem_dc"},
        {"rotulo_automatico": "ia.nuvem_dc", "rotulo_manual": "nenhuma"},
        {"rotulo_automatico": "a;b", "rotulo_manual": "b; a"},
        {"rotulo_automatico": "nenhuma", "rotulo_manual": ""},  # ainda não rotulada
    ]

    p = precisao(rotuladas)

    assert (p["rotuladas"], p["acertos"]) == (3, 2)
    assert p["precisao"] == pytest.approx(2 / 3)
    assert p["por_rotulo"]["ia.nuvem_dc"] == {"rotuladas": 2, "acertos": 1, "precisao": 0.5}


def test_nao_grava_a_amostra_dentro_do_repositorio(tmp_path):
    # O CSV tem frases de 10-Ks reais: fica na pasta compartilhada, nunca no repositório.
    with pytest.raises(ValueError):
        exigir_fora_do_repositorio(REPO / "backend" / "amostra.csv")
    exigir_fora_do_repositorio(tmp_path / "amostra.csv")
