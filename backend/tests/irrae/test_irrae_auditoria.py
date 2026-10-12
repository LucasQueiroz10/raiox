"""Calibração por retornos como auditoria (v1.1, seção 3; D-12 e D-15).

O diagnóstico compara o IrRAE fundamental com o estilo de mercado folha a folha e avisa quando
divergem. Nunca altera o IrRAE, usa um gerador de números aleatórios próprio e é pulado sem preços.
"""

import inspect

import numpy as np
import pandas as pd
import pytest

from irrae.calibracao import corte_bonferroni, diagnosticar

FOLHAS_COM_FATOR = ["nucleo", "ia.nuvem_dc", "ia.modelos_software"]
VERDADE = np.array([0.62, 0.25, 0.13])  # exposição de mercado verdadeira nas três folhas


def _mercado(semente=11, T=750):
    """Retornos sintéticos: três fatores correlacionados e uma empresa com a exposição VERDADE."""
    rng = np.random.default_rng(semente)
    C = 0.5 * np.ones((3, 3)) + 0.5 * np.eye(3)
    F = rng.multivariate_normal(np.zeros(3), 0.0001 * C, size=T)
    r = F @ VERDADE + rng.normal(0, 0.004, T)
    return r, pd.DataFrame(F, columns=FOLHAS_COM_FATOR)


def _irrae(tax, media_nas_folhas, conc=400, S=2000, semente=12):
    """Amostras (S, L) do IrRAE fundamental, com a média dada nas três folhas e zero nas outras."""
    alvo = np.zeros(tax.L)
    for f, m in zip(FOLHAS_COM_FATOR, media_nas_folhas, strict=True):
        alvo[tax.idx(f)] = m
    ativos = alvo > 0
    out = np.zeros((S, tax.L))
    out[:, ativos] = np.random.default_rng(semente).dirichlet(conc * alvo[ativos], size=S)
    return out


def test_corte_de_bonferroni_por_numero_de_folhas_testadas():
    assert corte_bonferroni(1) == pytest.approx(1.645, abs=1e-3)
    assert corte_bonferroni(6) == pytest.approx(2.394, abs=1e-3)


def test_sem_precos_o_diagnostico_e_pulado_sem_erro(tax):
    amostras = _irrae(tax, VERDADE)
    _, fatores = _mercado()

    assert diagnosticar(amostras, tax.folhas, None, fatores, semente=1) is None
    assert diagnosticar(amostras, tax.folhas, np.zeros(10), None, semente=1) is None
    assert diagnosticar(amostras, tax.folhas, np.zeros(10), pd.DataFrame(), semente=1) is None


def test_diagnostico_nunca_altera_o_irrae(tax):
    amostras = _irrae(tax, [0.55, 0.37, 0.08])
    copia = amostras.copy()
    amostras.flags.writeable = False  # qualquer escrita levantaria erro
    r, fatores = _mercado()

    diagnosticar(amostras, tax.folhas, r, fatores, semente=1)

    assert np.array_equal(amostras, copia)


def test_usa_gerador_proprio_e_e_reprodutivel(tax):
    # D-15: não recebe o gerador dos sorteios do IrRAE, só uma semente.
    assert "rng" not in inspect.signature(diagnosticar).parameters
    amostras = _irrae(tax, [0.55, 0.37, 0.08])
    r, fatores = _mercado()

    a = diagnosticar(amostras, tax.folhas, r, fatores, semente=7)
    b = diagnosticar(amostras, tax.folhas, r, fatores, semente=7)

    assert a == b


def test_alerta_na_folha_em_que_o_mercado_diverge_do_fundamental(tax):
    # Fundamental com a nuvem em 37% (verdade de mercado: 25%), como no experimento da seção 7.4.
    # O simplex obriga as outras folhas a divergirem também; aqui se confere a da nuvem.
    amostras = _irrae(tax, [0.55, 0.37, 0.08])
    r, fatores = _mercado()

    diag = {d.folha: d for d in diagnosticar(amostras, tax.folhas, r, fatores, semente=3)}

    assert set(diag) == set(FOLHAS_COM_FATOR)
    assert diag["ia.nuvem_dc"].alerta
    assert diag["ia.nuvem_dc"].z > corte_bonferroni(3)
    assert diag["ia.nuvem_dc"].media_fundamental == pytest.approx(0.37, abs=0.01)
    assert diag["ia.nuvem_dc"].beta == pytest.approx(0.25, abs=0.06)


def test_sem_alerta_quando_fundamental_e_mercado_concordam(tax):
    amostras = _irrae(tax, VERDADE)
    r, fatores = _mercado()

    diag = diagnosticar(amostras, tax.folhas, r, fatores, semente=3)

    assert not any(d.alerta for d in diag)


def test_folha_sem_fator_nao_e_testada_nem_conta_no_corte(tax):
    amostras = _irrae(tax, [0.55, 0.37, 0.08])
    r, fatores = _mercado()

    diag = diagnosticar(amostras, tax.folhas, r, fatores, semente=3)

    assert [d.folha for d in diag] == FOLHAS_COM_FATOR  # na ordem da taxonomia
    assert all(d.corte == pytest.approx(corte_bonferroni(3)) for d in diag)
