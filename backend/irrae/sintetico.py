"""Universo sintético com exposição VERDADEIRA conhecida.

Serve para: (1) testar se a fusão recupera a verdade; (2) medir quantas
empresas são necessárias para estimar a precisão (kappa) de cada fonte;
(3) comparar pesos fixos/iguais com pesos estimados; (4) medir escala.

Geração:
  w_c ~ Dirichlet(conc_setor * media_setor)                 (verdade)
  X_kc ~ Dirichlet(kappa_k * w_c)   [E com viés de 'hype']   (erro da fonte)
  medição: estimativa pontual e amostras em torno dela       (erro de medição)
    - R e N via contagens (Multinomial), o resto via Dirichlet com concentração variável
  faltantes: cada fonte some com probabilidade própria
"""

from __future__ import annotations

import numpy as np

from .componentes import Componente, ausente
from .taxonomia import Taxonomia

ARQUETIPOS = {
    "semicondutores": {"ia.semicondutores": 0.45, "ia.generica": 0.03},
    "software": {"ia.modelos_software": 0.20, "ia.nuvem_dc": 0.08, "ia.generica": 0.03},
    "nuvem": {"ia.nuvem_dc": 0.35, "ia.modelos_software": 0.08, "ia.generica": 0.02},
    "energia": {"ia.energia_dc": 0.20, "ia.generica": 0.01},
    "outros": {"ia.generica": 0.03, "ia.modelos_software": 0.02},
}

KAPPA_VERDADEIRO = {
    "A_receita": 40,
    "A_lucro": 15,
    "Ir_capex": 12,
    "B_backlog": 20,
    "R_patentes": 6,
    "N_narrativa": 5,
    "E_enquadramento": 3,
    "C_cadeia": 8,
    "P_participacoes": 4,
}
P_FALTA = {
    "A_receita": 0.02,
    "A_lucro": 0.15,
    "Ir_capex": 0.4,
    "B_backlog": 0.6,
    "R_patentes": 0.3,
    "N_narrativa": 0.1,
    "E_enquadramento": 0.3,
    "C_cadeia": 0.7,
    "P_participacoes": 0.8,
}
CONTAGEM = {
    "R_patentes": (4.0, 1.2),
    "N_narrativa": (5.5, 0.6),
}  # lognormal (mu, sigma) do nº de documentos/frases
HYPE = 1.8  # E super-representa folhas de IA
CONC_SETOR = 8.0


def gerar_universo(
    n: int,
    tax: Taxonomia,
    S: int,
    rng: np.random.Generator,
    conc_setor: float = CONC_SETOR,
    kappa_verdadeiro: dict | None = None,
    p_falta: dict | None = None,
):
    """Retorna (verdade, universo, setor):
    verdade: dict emp -> w (L,); universo: dict emp -> [Componente]; setor: dict emp -> str."""
    kv = kappa_verdadeiro or KAPPA_VERDADEIRO
    pf = p_falta or P_FALTA
    setores = list(ARQUETIPOS)
    verdade, universo, setor_de = {}, {}, {}
    for i in range(n):
        emp = f"E{i:05d}"
        st = setores[rng.integers(len(setores))]
        media = tax.vetor(ARQUETIPOS[st])
        w = rng.dirichlet(conc_setor * media)
        comps = []
        for k, kap in kv.items():
            if rng.random() < pf[k]:
                comps.append(ausente(k))
                continue
            alvo = w.copy()
            if k == "E_enquadramento":
                alvo[1:] *= HYPE
                alvo /= alvo.sum()
            x_fonte = rng.dirichlet(np.maximum(kap * alvo, 1e-3))
            if k in CONTAGEM:
                mu, sd = CONTAGEM[k]
                ndoc = max(1, int(rng.lognormal(mu, sd)))
                cont = rng.multinomial(ndoc, x_fonte)
                amostras = rng.dirichlet(cont + 0.5, size=S)
            else:
                mconc = rng.uniform(50, 400)
                x_hat = rng.dirichlet(np.maximum(mconc * x_fonte, 1e-3))
                amostras = rng.dirichlet(np.maximum(mconc * x_hat, 1e-3), size=S)
            comps.append(Componente(k, amostras))
        comps.append(Componente("prior_setorial", np.tile(media, (S, 1))))
        verdade[emp], universo[emp], setor_de[emp] = w, comps, st
    return verdade, universo, setor_de
