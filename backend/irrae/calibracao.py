"""Calibração externa com retornos: o "IrRAE de mercado".

Análise de estilo por retornos (Sharpe 1992): regride o retorno da ação nos
retornos de fatores (um por folha/tema + núcleo), com pesos >= 0 somando 1.
É a sensibilidade de mercado, não a exposição fundamental; serve para validar o
IrRAE e escolher hiperparâmetros (kappa, limiares, lambda).

Desde a v1.1 (especificação, seção 3) é só auditoria: o IrRAE final é o fundamental.
diagnosticar() compara os dois folha a folha e avisa quando divergem; nunca altera o IrRAE.

Intervalos por bootstrap em blocos (alternativa às aproximações de Lobosco &
DiBartolomeo 1997 e aos intervalos bayesianos de Kim, White & Stone 2005).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import nnls
from scipy.stats import norm


def estilo_sharpe(r: np.ndarray, F: np.ndarray, penal: float = 1e3) -> np.ndarray:
    """min ||r - F w||²  s.a. w >= 0, sum w = 1
    (NNLS com a restrição de soma via linha penalizada)."""
    escala = penal * max(1.0, float(np.abs(F).max()))
    A = np.vstack([F, escala * np.ones((1, F.shape[1]))])
    b = np.concatenate([r, [escala]])
    w, _ = nnls(A, b)
    s = w.sum()
    return w / s if s > 0 else w


def bootstrap_estilo(
    r: np.ndarray,
    F: np.ndarray,
    B: int = 300,
    bloco: int = 20,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Bootstrap em blocos móveis (preserva autocorrelação). Retorna (B, J)."""
    rng = rng or np.random.default_rng(0)
    T = len(r)
    n_blocos = int(np.ceil(T / bloco))
    out = np.empty((B, F.shape[1]))
    for b in range(B):
        ini = rng.integers(0, T - bloco + 1, size=n_blocos)
        idx = np.concatenate([np.arange(i, i + bloco) for i in ini])[:T]
        out[b] = estilo_sharpe(r[idx], F[idx])
    return out


def construir_fatores(
    retornos: pd.DataFrame,
    exposicoes: pd.DataFrame,
    limiar: float = 0.6,
    excluir: str | None = None,
    fator_nucleo: pd.Series | None = None,
) -> pd.DataFrame:
    """Fator de cada folha = média dos retornos das empresas 'puras' (exposição >= limiar) na folha.

    excluir: a empresa analisada sai dos fatores
    (evita circularidade: ela não pode explicar a si mesma).
    fator_nucleo: índice do SETOR OFICIAL da empresa (recomendado). Se None, usa empresas puras do
    núcleo (exposição ao núcleo >= limiar); se não houver, a média geral
    (que mistura temas e enviesa
    o peso do núcleo para cima).
    retornos: T x N (colunas = empresas); exposicoes: N x L (índice = empresas, colunas = folhas).
    """
    emp = [c for c in retornos.columns if c != excluir]
    fatores = {}
    for folha in exposicoes.columns:
        if folha == "nucleo" and fator_nucleo is not None:
            continue
        puras = [e for e in emp if e in exposicoes.index and exposicoes.loc[e, folha] >= limiar]
        if puras:
            fatores[folha] = retornos[puras].mean(axis=1)
    if fator_nucleo is not None:
        fatores["nucleo"] = fator_nucleo
    elif "nucleo" not in fatores:
        # sem empresas puras do núcleo: média geral
        # (ruim: mistura os temas; prefira um índice do setor oficial)
        fatores["nucleo"] = retornos[emp].mean(axis=1)
    return pd.DataFrame(fatores)


def combinar_fundamental_mercado(
    media_f: np.ndarray, var_f: np.ndarray, media_m: np.ndarray, var_m: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Combina o IrRAE fundamental (prior) com o estilo de mercado (verossimilhança) por precisão,
    folha a folha (aproximação gaussiana diagonal), e projeta de volta no simplex.
    Versão simples; a v2 deve fazer isso dentro do modelo bayesiano completo.

    Fora do cálculo da exposição desde a v1.1 (eq. 19; especificação, seção 3): fica só para
    pesquisa. O IrRAE final é o fundamental; use diagnosticar() para comparar com o mercado."""
    pf, pm = 1.0 / np.maximum(var_f, 1e-8), 1.0 / np.maximum(var_m, 1e-8)
    m = (pf * media_f + pm * media_m) / (pf + pm)
    v = 1.0 / (pf + pm)
    m = np.clip(m, 0, None)
    return m / m.sum(), v


@dataclass(frozen=True)
class DiagnosticoFolha:
    """Uma folha: IrRAE fundamental x estilo de mercado, cada um com a faixa estimada de 90%."""

    folha: str
    media_fundamental: float
    p05_fundamental: float
    p95_fundamental: float
    beta: float  # estimativa pontual do estilo de Sharpe
    p05_beta: float  # faixa pelo bootstrap em blocos
    p95_beta: float
    z: float
    corte: float
    alerta: bool  # z acima do corte: fundamental e mercado divergem nesta folha


def corte_bonferroni(m: int, alfa: float = 0.10) -> float:
    """Corte de |z| para m folhas testadas na mesma empresa (D-12; Dunn 1961).

    Sem correção, o corte de 1,645 por folha dá ~47% de chance de pelo menos um alarme falso em 6
    folhas. Com m = 6, o corte vira ~2,39."""
    return float(norm.ppf(1 - alfa / (2 * m)))


def diagnosticar(
    amostras: np.ndarray,
    folhas: Sequence[str],
    retornos: np.ndarray | None,
    fatores: pd.DataFrame | None,
    semente: int,
    B: int = 300,
    bloco: int = 20,
    alfa: float = 0.10,
) -> list[DiagnosticoFolha] | None:
    """Diagnóstico por folha (D-12): z = |m_f - beta| / sqrt(v_f + v_m), alerta se z > corte.

    amostras: (S, L) IrRAE da empresa (depois das regras), colunas na ordem de `folhas`. Só é lido.
    retornos: (T,) retornos da empresa; fatores: T x J, colunas = folhas que têm fator
    (construir_fatores). Folha sem fator não é testada nem conta no corte.
    semente: o diagnóstico usa um gerador próprio (D-15), para não mudar os sorteios do IrRAE.
    Sem preços (retornos ou fatores ausentes), devolve None: o módulo é pulado sem erro.
    """
    if retornos is None or fatores is None or fatores.empty:
        return None
    testadas = [f for f in folhas if f in fatores.columns]
    if not testadas:
        return None
    X = fatores[testadas].to_numpy()
    beta = estilo_sharpe(retornos, X)
    boot = bootstrap_estilo(retornos, X, B=B, bloco=bloco, rng=np.random.default_rng(semente))
    corte = corte_bonferroni(len(testadas), alfa)
    saida = []
    for j, folha in enumerate(testadas):
        x = amostras[:, list(folhas).index(folha)]
        m_f, v_f, v_m = float(x.mean()), float(x.var()), float(boot[:, j].var())
        dif = abs(m_f - float(beta[j]))
        z = dif / np.sqrt(v_f + v_m) if v_f + v_m > 0 else (np.inf if dif > 0 else 0.0)
        saida.append(
            DiagnosticoFolha(
                folha=folha,
                media_fundamental=m_f,
                p05_fundamental=float(np.quantile(x, 0.05)),
                p95_fundamental=float(np.quantile(x, 0.95)),
                beta=float(beta[j]),
                p05_beta=float(np.quantile(boot[:, j], 0.05)),
                p95_beta=float(np.quantile(boot[:, j], 0.95)),
                z=float(z),
                corte=corte,
                alerta=bool(z > corte),
            )
        )
    return saida
