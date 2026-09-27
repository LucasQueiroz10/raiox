"""Ferramentas para representar incerteza como amostras no simplex."""

from __future__ import annotations

import numpy as np

EPS = 1e-6


def beta_amostras(media: float, conc: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Beta parametrizada por média e concentração (a+b). conc alto = pouca incerteza."""
    media = float(np.clip(media, 0.0, 1.0))
    if media <= 0.0:
        return np.zeros(n)
    if media >= 1.0:
        return np.ones(n)
    return rng.beta(media * conc, (1 - media) * conc, size=n)


def dirichlet_amostras(
    media: np.ndarray, conc: float, n: int, rng: np.random.Generator
) -> np.ndarray:
    """Dirichlet centrada em 'media' (vetor no simplex). Zeros exatos continuam zero."""
    media = np.asarray(media, dtype=float)
    out = np.zeros((n, media.size))
    ativos = media > 0
    if ativos.sum() == 0:
        return out
    if ativos.sum() == 1:
        out[:, ativos] = 1.0
        return out
    m = media[ativos] / media[ativos].sum()
    out[:, ativos] = rng.dirichlet(np.maximum(m * conc, EPS), size=n)
    return out


def perturbar_dirichlet(amostras: np.ndarray, kappa: float, rng: np.random.Generator) -> np.ndarray:
    """Aplica o erro da fonte: Y ~ Dirichlet(kappa * X) para cada amostra X (linha).

    Usa o truque Gamma: Y_a = G_a / sum(G), G_a ~ Gamma(kappa*X_a).
    Folhas com X_a = 0 permanecem 0 (a fonte não inventa exposição onde não viu nada).
    """
    alpha = kappa * amostras
    g = np.where(alpha > 0, rng.gamma(np.maximum(alpha, EPS)), 0.0)
    s = g.sum(axis=1, keepdims=True)
    s[s == 0] = 1.0
    return g / s


def resumo(amostras: np.ndarray, q=(0.05, 0.95)) -> dict[str, np.ndarray]:
    """Média e quantis ao longo do eixo das amostras (eixo 0)."""
    return {
        "media": amostras.mean(axis=0),
        "p05": np.quantile(amostras, q[0], axis=0),
        "p95": np.quantile(amostras, q[1], axis=0),
    }


def variancia_total(amostras: np.ndarray) -> float:
    """Traço da covariância das amostras (soma das variâncias por folha)."""
    return float(amostras.var(axis=0).sum())
