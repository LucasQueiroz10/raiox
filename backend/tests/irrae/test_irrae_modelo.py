"""Testes do núcleo: conservação, hierarquia, ausente vs zero, pesos, regras, estimação de kappa."""

import numpy as np
import pytest

from irrae.componentes import (
    Componente,
    LinhaMapeamento,
    ausente,
    de_contagens,
    de_etfs,
    de_heranca,
    de_receita_futura,
    de_segmentos,
    prior_setorial,
)
from irrae.fusao import estimar_kappas, fundir_momentos, pesos_variancia_minima
from irrae.modelo import calcular_empresa, kappas_prior
from irrae.regras import aplicar_regras
from irrae.sintetico import KAPPA_VERDADEIRO, gerar_universo

S = 1000


def _linha(frac, split, conc=20):
    return LinhaMapeamento(frac, conc, split, 20, "habilitador")


# ---------- componentes ----------


def test_segmentos_conservam_e_tratam_negativos(tax, rng):
    mapa = {"Nuvem": _linha(0.5, {"ia.nuvem_dc": 1.0}), "Varejo": _linha(0.0, {"ia.generica": 1.0})}
    c = de_segmentos("A_lucro", {"Nuvem": 30, "Varejo": -10, "SemMapa": 10}, mapa, tax, S, rng)
    assert np.allclose(c.amostras.sum(axis=1), 1)
    assert any("negativos" in a for a in c.avisos) and any("sem mapeamento" in a for a in c.avisos)
    # Nuvem = 30/40 da base positiva; metade dela vai para ia.nuvem_dc
    assert c.media[tax.idx("ia.nuvem_dc")] == pytest.approx(0.75 * 0.5, abs=0.03)


def test_subtema_nunca_maior_que_tema(tax, rng):
    mapa = {"X": _linha(0.6, {"ia.nuvem_dc": 0.5, "ia.semicondutores": 0.5})}
    c = de_segmentos("A_receita", {"X": 1}, mapa, tax, S, rng)
    tema = tax.agregar_temas(c.amostras)["ia"]
    for i in tax.indices_do_tema("ia"):
        assert (c.amostras[:, i] <= tema + 1e-12).all()


def test_ausente_e_diferente_de_zero(tax, rng):
    sem_patentes = de_contagens("R_patentes", {}, total=0, tax=tax, S=S, rng=rng)
    zero_ia = de_contagens("R_patentes", {}, total=500, tax=tax, S=S, rng=rng)
    assert not sem_patentes.ok
    assert zero_ia.ok and zero_ia.media[0] > 0.99


def test_poucas_contagens_dao_intervalo_largo(tax, rng):
    poucas = de_contagens("R_patentes", {"ia.modelos_software": 2}, total=10, tax=tax, S=S, rng=rng)
    muitas = de_contagens(
        "R_patentes", {"ia.modelos_software": 200}, total=1000, tax=tax, S=S, rng=rng
    )
    i = tax.idx("ia.modelos_software")
    assert poucas.amostras[:, i].std() > 3 * muitas.amostras[:, i].std()


def test_etfs_e_heranca(tax, rng):
    e = de_etfs(
        "E_enquadramento",
        [
            ("AIQ", "ia.modelos_software", 30.0),
            ("SMH", "ia.semicondutores", 10.0),
            ("SPY", "nucleo", 60.0),
        ],
        tax,
        S,
        rng,
    )
    assert np.allclose(e.amostras.sum(axis=1), 1) and e.media[0] > 0.4
    w_cliente = tax.vetor({"ia.nuvem_dc": 0.8})
    alta = de_heranca("C_cadeia", [(0.9, w_cliente)], tax, S, rng)
    baixa = de_heranca("C_cadeia", [(0.1, w_cliente)], tax, S, rng)
    i = tax.idx("ia.nuvem_dc")
    assert alta.media[i] == pytest.approx(0.8, abs=0.05)
    assert baixa.amostras[:, i].std() > alta.amostras[:, i].std()  # cobertura baixa => mais incerto


def test_receita_futura_nao_vira_100pct_backlog(tax, rng):
    mapa = {
        "Nuvem": _linha(1.0, {"ia.nuvem_dc": 1.0}, conc=1000),
        "Outro": _linha(0.0, {"ia.generica": 1}),
    }
    c = de_receita_futura(
        "B_backlog",
        {"Nuvem": 10, "Outro": 90},
        mapa,
        [(100.0, mapa["Nuvem"])],
        tax,
        S,
        rng,
        horizonte=(4, 4),
    )
    # (10 + 100/4) / (100 + 25) = 0.28
    assert c.media[tax.idx("ia.nuvem_dc")] == pytest.approx(0.28, abs=0.01)


# ---------- fusão ----------


def test_pesos_variancia_minima_igual_ao_otimizador():
    from scipy.optimize import minimize

    r = np.random.default_rng(0)
    for _ in range(50):
        K = r.integers(2, 8)
        v = r.uniform(0.01, 1, K)
        A = r.uniform(-0.3, 0.9, (K, K))
        rho = np.clip((A + A.T) / 2, -0.2, 0.9)
        np.fill_diagonal(rho, 1)
        if np.linalg.eigvalsh(rho).min() <= 0.05:
            continue
        p = pesos_variancia_minima(v, rho)
        sd = np.sqrt(v)
        Sig = rho * np.outer(sd, sd)
        ref = minimize(
            lambda x: x @ Sig @ x,  # noqa: B023 - usado na mesma iteração
            np.ones(K) / K,
            method="SLSQP",
            bounds=[(0, 1)] * K,
            constraints=[{"type": "eq", "fun": lambda x: x.sum() - 1}],
            options={"ftol": 1e-14},
        )
        assert p.sum() == pytest.approx(1) and (p >= 0).all()
        assert p @ Sig @ p <= ref.fun + 1e-9


def test_fonte_mais_precisa_ganha_peso_e_correlacao_divide(tax, rng):
    w = tax.vetor({"ia.nuvem_dc": 0.3})
    a = Componente("A_receita", rng.dirichlet(500 * w, size=S))
    b = Componente("A_lucro", rng.dirichlet(500 * w, size=S))
    n = Componente("N_narrativa", rng.dirichlet(500 * w, size=S))
    kap = {"A_receita": 30, "A_lucro": 30, "N_narrativa": 5}
    f0 = fundir_momentos([a, b, n], kap, {}, lam=0.0)
    assert f0.pesos[0] > f0.pesos[2]
    f1 = fundir_momentos([a, b, n], kap, {"A_receita|A_lucro": 0.9}, lam=0.0)
    assert f1.pesos[0] + f1.pesos[1] < f0.pesos[0] + f0.pesos[1]


def test_so_prior_quando_nao_ha_dado(cfg, tax, rng):
    comps = [ausente("A_receita"), prior_setorial("3674", cfg["prior"], tax, S, rng)]
    res = calcular_empresa("X", comps, cfg, kappas_prior(cfg["componentes"]), rng)
    assert res.fusao.nomes == ["prior_setorial"] and res.selo == "preliminar"


def test_resultado_conserva_soma(cfg, tax, rng):
    mapa = {
        "Nuvem": _linha(0.5, {"ia.nuvem_dc": 0.8, "ia.modelos_software": 0.2}),
        "Varejo": _linha(0.03, {"ia.generica": 1}),
    }
    comps = [
        de_segmentos("A_receita", {"Nuvem": 20, "Varejo": 80}, mapa, tax, S, rng),
        de_segmentos("A_lucro", {"Nuvem": 15, "Varejo": 5}, mapa, tax, S, rng),
        prior_setorial("5961", cfg["prior"], tax, S, rng),
    ]
    res = calcular_empresa("X", comps, cfg, kappas_prior(cfg["componentes"]), rng)
    assert np.allclose(res.amostras.sum(axis=1), 1)
    assert np.allclose(res.amostras_brutas.sum(axis=1), 1)


# ---------- regras ----------


def _F(tax, pesos, n=200):
    return np.tile(tax.vetor(pesos), (n, 1))


def test_subtema_pequeno_vai_para_generica_nao_para_nucleo(tax):
    regras = {"limiar_entrada": 0.06, "limiar_saida": 0.04, "suporte_minimo_nao_percepcao": 0.01}
    F = _F(tax, {"ia.nuvem_dc": 0.04, "ia.semicondutores": 0.04, "ia.modelos_software": 0.04})
    sup = F.mean(0)
    F2, ativos, _ = aplicar_regras(F, tax, sup, regras)
    assert F2[:, tax.idx("ia.generica")].mean() == pytest.approx(0.12)
    assert "ia" in ativos and np.allclose(F2.sum(1), 1)


def test_tema_pequeno_vai_para_nucleo_e_histerese(tax):
    regras = {"limiar_entrada": 0.06, "limiar_saida": 0.04, "suporte_minimo_nao_percepcao": 0.01}
    F = _F(tax, {"ia.nuvem_dc": 0.05})
    F2, ativos, _ = aplicar_regras(F, tax, F.mean(0), regras)  # não entra (5% < 6%)
    assert F2[:, 0].mean() == pytest.approx(1.0) and "ia" not in ativos
    F3, ativos3, _ = aplicar_regras(
        F, tax, F.mean(0), regras, {"ia", "ia.nuvem_dc"}
    )  # já ativo: fica (5% > 4%)
    assert F3[:, tax.idx("ia.nuvem_dc")].mean() == pytest.approx(0.05) and "ia.nuvem_dc" in ativos3


def test_percepcao_sozinha_nao_cria_tema(tax):
    regras = {"limiar_entrada": 0.06, "limiar_saida": 0.04, "suporte_minimo_nao_percepcao": 0.01}
    F = _F(tax, {"ia.energia_dc": 0.10})
    sup = np.zeros(tax.L)  # nenhuma fonte "dura" viu energia
    F2, _, log = aplicar_regras(F, tax, sup, regras)
    assert F2[:, tax.idx("ia.energia_dc")].sum() == 0 and any("percepção" in l for l in log)  # noqa: E741


# ---------- estimação de kappa (universo sintético) ----------


def test_kappa_estimado_ordena_fontes(cfg, tax):
    rng = np.random.default_rng(7)
    verdade, universo, _ = gerar_universo(400, tax, 200, rng)
    kp = kappas_prior(cfg["componentes"])
    k_est, diag = estimar_kappas(universo, kp, cfg["componentes"]["correlacao_erros"], n0=5)
    from scipy.stats import spearmanr

    nomes = list(KAPPA_VERDADEIRO)
    rho = spearmanr([KAPPA_VERDADEIRO[n] for n in nomes], [k_est[n] for n in nomes]).correlation
    assert rho > 0.7
