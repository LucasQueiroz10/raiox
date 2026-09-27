"""Fusão dos componentes: onde os pesos são otimizados.

Modelo de observação (versão v1, por momentos):
    cada fonte k enxerga a exposição verdadeira w da empresa com erro próprio:
        X_k ~ Dirichlet(kappa_k * w)            (erro da fonte, "source error")
    e ainda tem incerteza de medição/mapeamento (as amostras do componente).

Variância total da fonte k na empresa c (traço):
    v_kc = tr Var(amostras_k)  +  (1 - sum(w^2)) / (kappa_k + 1)

Pesos = combinação de variância mínima (Bates & Granger 1969), com correlação
entre erros (GLS / Aitken) e restrição p >= 0, sum p = 1:
    min p' Σ p   s.a.  p >= 0, 1'p = 1,   Σ_kl = rho_kl sqrt(v_k v_l)
Depois encolhe para pesos iguais (Smith & Wallis 2009): p = (1-λ) p* + λ p_igual.

kappa_k é reestimado com o universo de empresas (estimar_kappas), na lógica de
Dawid & Skene (1979): sem gabarito, a confiabilidade de cada fonte sai da
concordância com as demais.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from .componentes import Componente
from .distribuicoes import perturbar_dirichlet

PRIOR = "prior_setorial"


def matriz_rho(nomes: list[str], cfg_corr: dict) -> np.ndarray:
    K = len(nomes)
    R = np.eye(K)
    for chave, r in cfg_corr.items():
        if chave.startswith("_"):
            continue
        a, b = chave.split("|")
        if a in nomes and b in nomes:
            i, j = nomes.index(a), nomes.index(b)
            R[i, j] = R[j, i] = r
    return R


def pesos_variancia_minima(v: np.ndarray, rho: np.ndarray) -> np.ndarray:
    """min p'Σp s.a. p>=0, soma 1. Conjunto ativo com checagem KKT; SLSQP como reserva."""
    K = len(v)
    if K == 1:
        return np.ones(1)
    v = np.maximum(v, 1e-12)
    sd = np.sqrt(v)
    Sig = rho * np.outer(sd, sd) + 1e-12 * np.eye(K)
    ativo = np.ones(K, bool)
    for _ in range(3 * K):
        idx = np.where(ativo)[0]
        Si = np.linalg.solve(Sig[np.ix_(idx, idx)], np.ones(len(idx)))
        p = np.zeros(K)
        p[idx] = Si / Si.sum()
        if (p[idx] < -1e-12).any():
            ativo[idx[np.argmin(p[idx])]] = False
            continue
        g = Sig @ p  # KKT: g_i = mu nos ativos, g_i >= mu nos inativos
        mu = g[idx].mean()
        viol = np.where(~ativo & (g < mu - 1e-10))[0]
        if len(viol) == 0:
            return np.clip(p, 0, None) / np.clip(p, 0, None).sum()
        ativo[viol[np.argmin(g[viol])]] = True
    res = minimize(
        lambda x: x @ Sig @ x,
        np.ones(K) / K,
        method="SLSQP",
        bounds=[(0, 1)] * K,
        constraints=[{"type": "eq", "fun": lambda x: x.sum() - 1}],
    )
    p = np.clip(res.x, 0, None)
    return p / p.sum()


@dataclass
class Fusao:
    nomes: list[str]
    pesos: np.ndarray  # (K,)
    variancias: np.ndarray  # (K,) v_kc
    medias: np.ndarray  # (K, L)
    media_fundida: np.ndarray  # (L,)
    var_fundida: float  # p'Σp (traço aproximado)


def fundir_momentos(
    comps: list[Componente], kappas: dict[str, float], cfg_corr: dict, lam: float = 0.3
) -> Fusao | None:
    """Pesos e média fundida sem sortear
    (rápido; usado na estimação de kappa e na sensibilidade)."""
    disp = [c for c in comps if c.ok]
    if not disp:
        return None
    nomes = [c.nome for c in disp]
    medias = np.vstack([c.amostras.mean(axis=0) for c in disp])
    u = np.array([c.amostras.var(axis=0).sum() for c in disp])
    w0 = medias.mean(axis=0)  # 1ª passada: centro para o erro da fonte
    g = 1.0 - float((w0**2).sum())
    v = u + g / (np.array([kappas[n] for n in nomes]) + 1.0)
    rho = matriz_rho(nomes, cfg_corr)
    p_opt = pesos_variancia_minima(v, rho)
    reais = np.array([n != PRIOR for n in nomes])
    if reais.any():
        p_igual = reais / reais.sum()  # pesos iguais só entre fontes reais
        p = (1 - lam) * p_opt + lam * p_igual
    else:
        p = p_opt
    sd = np.sqrt(v)
    var_f = float(p @ (rho * np.outer(sd, sd)) @ p)
    return Fusao(nomes, p, v, medias, p @ medias, var_f)


def fundir_amostras(
    comps: list[Componente], fusao: Fusao, kappas: dict[str, float], rng: np.random.Generator
) -> np.ndarray:
    """Amostras da exposição fundida: cada fonte recebe seu erro de fonte e é somada com os pesos.
    (v1: os erros são sorteados independentes; a correlação entra só nos pesos.)"""
    disp = {c.nome: c for c in comps if c.ok}
    F = None
    for nome, p in zip(fusao.nomes, fusao.pesos, strict=True):
        if p <= 0:
            continue
        Y = perturbar_dirichlet(disp[nome].amostras, kappas[nome], rng)
        F = p * Y if F is None else F + p * Y
    return F


def estimar_kappas(
    universo: dict[str, list[Componente]],
    kappa_prior: dict[str, float],
    cfg_corr: dict,
    lam: float = 0.3,
    n0: float = 20.0,
    iters: int = 8,
    limites=(0.5, 1000.0),
    fixos: tuple[str, ...] = (),
    n_min: int = 30,
) -> tuple[dict[str, float], dict]:
    """Reestima a precisão de cada fonte pela discordância com as demais (deixa-uma-fonte-de-fora).

    Para a fonte k na empresa c:  d = ||m_k - ŵ_(-k)||²  ≈  u_k + e_k + var(ŵ_(-k))
    => e_k (erro da fonte) = d - u_k - var(ŵ_(-k));   kappa_k = média(1-Σŵ²)/média(e_k) - 1
    Encolhe em log para kappa_prior com n0 pseudo-empresas:
    com poucas empresas, fica perto do prior.
    'fixos' não são reestimados. Fontes observadas em menos de n_min empresas mantêm o prior
    (com poucas empresas a estimativa bruta oscila entre os limites;
    ver resultados/kappas_demo.csv).
    Limitação conhecida (v1): ignora a correlação entre erros na estimação e tende a superestimar
    kappa de fontes muito precisas (~15% no universo sintético com 1.500 empresas).
    """
    kappas = dict(kappa_prior)
    diag = {}
    for _ in range(iters):
        acum: dict[str, list[tuple[float, float]]] = {k: [] for k in kappas}
        for comps in universo.values():
            disp = [c for c in comps if c.ok]
            if len(disp) < 2:
                continue
            f_all = fundir_momentos(disp, kappas, cfg_corr, lam)
            g = 1.0 - float((f_all.media_fundida**2).sum())
            for c in disp:
                if c.nome in fixos:
                    continue
                outros = [o for o in disp if o.nome != c.nome]
                f_o = fundir_momentos(outros, kappas, cfg_corr, lam)
                m_k = c.amostras.mean(axis=0)
                d = float(((m_k - f_o.media_fundida) ** 2).sum())
                u = float(c.amostras.var(axis=0).sum())
                acum[c.nome].append((d - u - f_o.var_fundida, g))
        novo = {}
        for k, lst in acum.items():
            if not lst:
                novo[k] = kappas[k]
                diag[k] = {"n": 0, "kappa_bruto": None}
                continue
            if len(lst) < n_min:
                e_ = np.array([x[0] for x in lst])
                g_ = np.array([x[1] for x in lst])
                novo[k] = kappa_prior[k]
                diag[k] = {
                    "n": len(lst),
                    "kappa_bruto": float(np.clip(g_.mean() / max(e_.mean(), 1e-6) - 1, *limites)),
                    "obs": f"n < {n_min}: mantém o prior",
                }
                continue
            e = np.array([x[0] for x in lst])
            gg = np.array([x[1] for x in lst])
            e_med = max(float(e.mean()), 1e-6)
            k_bruto = float(np.clip(gg.mean() / e_med - 1.0, *limites))
            n = len(lst)
            novo[k] = float(np.exp((n * np.log(k_bruto) + n0 * np.log(kappa_prior[k])) / (n + n0)))
            diag[k] = {"n": n, "kappa_bruto": k_bruto}
        kappas = novo
    for k in diag:
        diag[k]["kappa_final"] = kappas[k]
    return kappas, diag
