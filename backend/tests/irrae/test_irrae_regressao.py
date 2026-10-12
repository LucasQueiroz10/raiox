"""Regressão com um universo sintético congelado (D-16 da v1.1).

tests/fixtures/irrae_universo_congelado.json foi gerado uma vez por irrae/sintetico.py, ANTES da
remoção do componente E, e o E foi retirado dele. Rodar o gerador de novo não serviria: sem o E
a sequência de sorteios muda e todas as empresas saem diferentes. Por isso cada componente guarda
a Dirichlet (alpha) das suas amostras e é sorteado de novo aqui com uma semente própria; o prior
guarda a média. Os resultados esperados usam os kappas do prior (config/componentes.json), não a
reestimação com o universo, e uma semente por empresa.

Se uma mudança alterar estes números, é mudança de metodologia: só com aprovação do M1 (ADR 0004).
Nesse caso, recalcule o "esperado" de cada empresa com _resultado no mesmo PR e explique a
diferença.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from irrae.componentes import Componente
from irrae.modelo import calcular_empresa, kappas_prior

ARQUIVO = Path(__file__).resolve().parents[1] / "fixtures" / "irrae_universo_congelado.json"
UNIVERSO = json.loads(ARQUIVO.read_text(encoding="utf-8"))
TOLERANCIA = 1e-9  # só ponto flutuante (a libm muda entre Windows e Linux)


def _componentes(empresa: dict, S: int) -> list[Componente]:
    comps = []
    for posicao, c in enumerate(empresa["componentes"]):
        if "media" in c:
            comps.append(Componente(c["nome"], np.tile(np.array(c["media"]), (S, 1))))
        else:
            rng = np.random.default_rng([empresa["semente"], posicao])
            comps.append(Componente(c["nome"], rng.dirichlet(np.array(c["alpha"]), size=S)))
    return comps


def _resultado(empresa: dict, cfg: dict) -> dict:
    r = calcular_empresa(
        empresa["id"],
        _componentes(empresa, UNIVERSO["S"]),
        cfg,
        kappas_prior(cfg["componentes"]),
        np.random.default_rng(empresa["semente"]),
    )
    t = r.tabela(cfg["taxonomia"])
    return {
        "areas": {
            a: [float(m), float(p05), float(p95)]
            for a, m, p05, p95 in zip(t.area, t.media, t.p05, t.p95, strict=True)
        },
        "selo": r.selo,
        "pesos": {n: float(p) for n, p in zip(r.fusao.nomes, r.fusao.pesos, strict=True)},
    }


@pytest.mark.parametrize("empresa", UNIVERSO["empresas"], ids=lambda e: e["id"])
def test_universo_congelado_da_o_mesmo_resultado(empresa, cfg):
    obtido = _resultado(empresa, cfg)
    esperado = empresa["esperado"]

    assert obtido["selo"] == esperado["selo"]
    assert obtido["pesos"] == pytest.approx(esperado["pesos"], abs=TOLERANCIA)
    assert obtido["areas"].keys() == esperado["areas"].keys()
    for area, valores in esperado["areas"].items():
        assert obtido["areas"][area] == pytest.approx(valores, abs=TOLERANCIA), area


def test_universo_congelado_nao_tem_o_componente_e():
    nomes = {c["nome"] for e in UNIVERSO["empresas"] for c in e["componentes"]}

    assert "E_enquadramento" not in nomes
    assert {"A_receita", "N_narrativa", "prior_setorial"} <= nomes
