import numpy as np
import pandas as pd
import pytest

from irrae.calibracao import (
    bootstrap_estilo,
    combinar_fundamental_mercado,
    construir_fatores,
    estilo_sharpe,
)
from irrae.temporal import kalman_nivel_local


def test_estilo_sharpe_recupera_pesos():
    rng = np.random.default_rng(1)
    T, J = 750, 4
    C = 0.5 * np.ones((J, J)) + 0.5 * np.eye(J)  # fatores correlacionados
    F = rng.multivariate_normal(np.zeros(J), 0.0001 * C, size=T)
    w = np.array([0.6, 0.25, 0.15, 0.0])
    r = F @ w + rng.normal(0, 0.004, T)
    w_hat = estilo_sharpe(r, F)
    assert w_hat.sum() == pytest.approx(1) and (w_hat >= 0).all()
    assert np.abs(w_hat - w).max() < 0.1
    B = bootstrap_estilo(r, F, B=200, rng=rng)
    lo, hi = np.quantile(B, [0.05, 0.95], axis=0)
    assert ((lo - 0.02 <= w) & (w <= hi + 0.02)).mean() >= 0.75


def test_fatores_excluem_a_propria_empresa():
    ret = pd.DataFrame(np.random.default_rng(2).normal(size=(50, 3)), columns=["A", "B", "C"])
    expo = pd.DataFrame(
        {"nucleo": [0.2, 0.3, 0.9], "ia.nuvem_dc": [0.8, 0.7, 0.1]}, index=["A", "B", "C"]
    )
    f = construir_fatores(ret, expo, limiar=0.6, excluir="A")
    assert np.allclose(f["ia.nuvem_dc"], ret["B"])


def test_combinacao_fica_entre_as_duas():
    m, v = combinar_fundamental_mercado(
        np.array([0.7, 0.3]), np.array([0.01, 0.01]), np.array([0.5, 0.5]), np.array([0.01, 0.01])
    )
    assert m[1] == pytest.approx(0.4) and m.sum() == pytest.approx(1)


def test_kalman_suaviza():
    rng = np.random.default_rng(3)
    T = 40
    verdade = np.column_stack([np.linspace(0.8, 0.7, T), np.linspace(0.2, 0.3, T)])
    ruido = 0.05
    y = np.clip(verdade + rng.normal(0, ruido, (T, 2)), 0, 1)
    M, _ = kalman_nivel_local(y, np.full((T, 2), ruido**2), q=1e-4)
    assert np.mean((M - verdade) ** 2) < 0.5 * np.mean((y - verdade) ** 2)
    assert np.allclose(M.sum(1), 1)
