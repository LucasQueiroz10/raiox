"""Exposição herdada pela rede de clientes (e participações).

Um fornecedor que vende 40% para empresas muito expostas a IA herda parte dessa
exposição (ligações econômicas propagam retornos: Cohen & Frazzini 2008).
Útil para temas indiretos como "Energia para data centers".

Fonte pública típica: clientes que representam >= 10% da receita (divulgação
exigida pelo ASC 280 nas notas do 10-K). A cobertura costuma ser parcial,
por isso o componente carrega 'cobertura' e fica mais incerto quando ela é baixa.
"""

from __future__ import annotations

import numpy as np

from .componentes import Componente, de_heranca
from .taxonomia import Taxonomia


def componentes_cadeia(
    clientes: dict[str, list[tuple[str, float]]],
    exposicao: dict[str, np.ndarray],
    tax: Taxonomia,
    S: int,
    rng: np.random.Generator,
    nome: str = "C_cadeia",
) -> dict[str, Componente]:
    """clientes: empresa -> [(cliente, fração da receita)]; exposicao: empresa -> vetor médio (L,).
    Clientes sem exposição conhecida são ignorados (reduzem a cobertura)."""
    out = {}
    for emp, lista in clientes.items():
        parceiros = [(f, exposicao[c]) for c, f in lista if c in exposicao and f > 0]
        out[emp] = de_heranca(nome, parceiros, tax, S, rng, fonte="clientes >=10% (ASC 280)")
    return out


def propagar(
    clientes: dict[str, list[tuple[str, float]]],
    calcular: callable,
    empresas: list[str],
    iters: int = 3,
) -> dict[str, np.ndarray]:
    """Ponto fixo simples: calcula exposições, gera C_cadeia a partir delas, recalcula.
    'calcular(empresa, componentes_cadeia_ou_None) -> vetor médio' é fornecido pelo chamador."""
    expo = {e: calcular(e, None) for e in empresas}
    for _ in range(iters):
        expo = {e: calcular(e, (clientes.get(e), expo)) for e in empresas}
    return expo
