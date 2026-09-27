from pathlib import Path

import numpy as np
import pytest

from ingest.nport import parse_nport
from irrae.agregacao import exposicao_etf, pesos_da_carteira, posicoes_sem_etf
from irrae.componentes import de_etfs

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def _amostras(tax, rng, pesos, conc=60, S=2000):
    return rng.dirichlet(np.maximum(conc * tax.vetor(pesos), 1e-3), size=S)


def test_etf_conserva_e_separa_nao_coberto(tax, rng):
    am = {
        "A": _amostras(tax, rng, {"ia.nuvem_dc": 0.4}),
        "B": _amostras(tax, rng, {"ia.semicondutores": 0.7}),
    }
    r = exposicao_etf("X", {"A": 0.5, "B": 0.3, "CAIXA": 0.2}, am, tax, rng)
    folhas = r.media[: tax.L].sum()
    assert r.cobertura == pytest.approx(0.8)
    assert folhas + r.media[-1] == pytest.approx(1.0)
    ia = r.colunas.index("ia")
    esperado = 0.5 * am["A"][:, 1:].sum(1).mean() + 0.3 * am["B"][:, 1:].sum(1).mean()
    assert r.media[ia] == pytest.approx(esperado, abs=0.01)


def test_comonotonico_mais_largo_e_quantis_somam(tax, rng):
    am = {k: _amostras(tax, rng, {"ia.nuvem_dc": 0.3}, conc=20) for k in "ABCD"}
    pesos = {k: 0.25 for k in "ABCD"}
    r = exposicao_etf("X", pesos, am, tax, rng)
    ia = r.colunas.index("ia")
    assert r.p05_comon[ia] <= r.p05_indep[ia] + 1e-9 and r.p95_comon[ia] >= r.p95_indep[ia] - 1e-9
    # conferência explícita: soma de amostras ordenadas (acoplamento comonotônico)
    tema = {k: np.sort(v[:, 1:].sum(1)) for k, v in am.items()}
    soma = sum(0.25 * t for t in tema.values())
    assert np.quantile(soma, 0.95) == pytest.approx(r.p95_comon[ia], abs=0.005)


def test_sem_etf_muda_o_componente_e(tax, rng):
    pos = [("AIQ", "ia.modelos_software", 80.0), ("SPY", "nucleo", 20.0)]
    com = de_etfs("E_enquadramento", pos, tax, 500, rng)
    sem = de_etfs("E_enquadramento", posicoes_sem_etf(pos, "AIQ"), tax, 500, rng)
    assert com.media[tax.idx("ia.modelos_software")] > 0.5
    assert sem.media[0] == pytest.approx(1.0)


def test_pesos_da_carteira_nport():
    _, cart = parse_nport((FIX / "nport_min.xml").read_bytes())
    p = pesos_da_carteira(cart, {"000000AA1": "EMPA"})
    assert p == {"EMPA": pytest.approx(0.0505)}
