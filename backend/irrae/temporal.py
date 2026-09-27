"""Estabilidade no tempo: filtro de Kalman de nível local por folha.

Exposição muda devagar; o filtro pondera o dado novo pela sua incerteza
(variância do intervalo) contra a persistência (ruído de processo q).
Dado muito incerto => o filtro quase não se move. Depois reprojeta no simplex.
(Harvey 1989, modelos estruturais de séries temporais.)
"""

from __future__ import annotations

import numpy as np


def kalman_nivel_local(
    y: np.ndarray,
    r: np.ndarray,
    q: float | np.ndarray = 1e-4,
    m0: np.ndarray | None = None,
    p0: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """y: (T, L) médias por período; r: (T, L) variâncias de medição; q: variância do passo.
    Retorna médias e variâncias filtradas (T, L), com as médias renormalizadas para somar 1."""
    T, L = y.shape
    m = np.array(y[0] if m0 is None else m0, dtype=float)
    P = np.full(L, p0)
    M, V = np.empty((T, L)), np.empty((T, L))
    for t in range(T):
        P = P + q
        K = P / (P + r[t])
        m = m + K * (y[t] - m)
        P = (1 - K) * P
        mm = np.clip(m, 0, None)
        M[t] = mm / mm.sum() if mm.sum() > 0 else mm
        V[t] = P
    return M, V
