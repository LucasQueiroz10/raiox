"""Orquestra o cálculo do IrRAE de uma empresa: fusão -> amostras -> regras -> resumo."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .componentes import Componente
from .distribuicoes import resumo
from .fusao import PRIOR, Fusao, fundir_amostras, fundir_momentos
from .regras import aplicar_regras, selo
from .taxonomia import Taxonomia


def carregar_config(pasta: str | Path) -> dict:
    pasta = Path(pasta)
    return {
        "taxonomia": Taxonomia.carregar(pasta / "taxonomia.json"),
        "componentes": json.loads((pasta / "componentes.json").read_text(encoding="utf-8")),
        "prior": json.loads((pasta / "prior_setorial.json").read_text(encoding="utf-8")),
    }


def kappas_prior(cfg_comp: dict) -> dict[str, float]:
    return {k: float(v["kappa_prior"]) for k, v in cfg_comp["componentes"].items()}


@dataclass
class ResultadoEmpresa:
    empresa: str
    fusao: Fusao
    amostras_brutas: np.ndarray
    amostras: np.ndarray  # após regras
    ativos: set[str]
    selo: str
    largura_max: float
    log_regras: list[str]
    componentes_ausentes: list[str]
    papel: dict[str, float] = field(default_factory=dict)

    def tabela(self, tax: Taxonomia) -> pd.DataFrame:
        linhas = []
        r = resumo(self.amostras)
        for i, f in enumerate(tax.folhas):
            linhas.append(
                {
                    "empresa": self.empresa,
                    "nivel": "folha",
                    "area": f,
                    "nome": tax.nomes[f],
                    "media": r["media"][i],
                    "p05": r["p05"][i],
                    "p95": r["p95"][i],
                }
            )
        for t, x in tax.agregar_temas(self.amostras).items():
            if t == "nucleo":
                continue
            linhas.append(
                {
                    "empresa": self.empresa,
                    "nivel": "tema",
                    "area": t,
                    "nome": tax.nomes[t],
                    "media": x.mean(),
                    "p05": np.quantile(x, 0.05),
                    "p95": np.quantile(x, 0.95),
                }
            )
        df = pd.DataFrame(linhas)
        df["selo"] = self.selo
        return df


def calcular_empresa(
    empresa: str,
    comps: list[Componente],
    cfg: dict,
    kappas: dict[str, float],
    rng: np.random.Generator,
    ativos_anteriores: set[str] | None = None,
) -> ResultadoEmpresa:
    tax: Taxonomia = cfg["taxonomia"]
    cc = cfg["componentes"]
    lam = cc["fusao"]["shrinkage_lambda"]
    fus = fundir_momentos(comps, kappas, cc["correlacao_erros"], lam)
    F = fundir_amostras(comps, fus, kappas, rng)

    # suporte de fontes que não são percepção nem prior (para a regra "percepção não cria tema")
    pilar = {k: v["pilar"] for k, v in cc["componentes"].items()}
    suporte, sup_perc = np.zeros(tax.L), np.zeros(tax.L)
    for n, p, m in zip(fus.nomes, fus.pesos, fus.medias, strict=True):
        if pilar.get(n) == "percepcao":
            sup_perc += p * m
        elif pilar.get(n) != "prior":
            suporte += p * m
    F2, ativos, log = aplicar_regras(F, tax, suporte, cc["regras"], ativos_anteriores, sup_perc)
    n_reais = sum(1 for c in comps if c.ok and c.nome != PRIOR)
    s, lmax = selo(F2, tax, ativos, n_reais, cc["regras"])

    # papel na cadeia (produtor/habilitador/adotante) a partir dos componentes que o informam
    papel: dict[str, float] = {}
    for c in comps:
        if c.ok and c.papel and c.nome in fus.nomes:
            p = fus.pesos[fus.nomes.index(c.nome)]
            for nome_papel, vec in c.papel.items():
                papel[nome_papel] = papel.get(nome_papel, 0.0) + p * float(vec.sum())
    tot = sum(papel.values())
    papel = {k: v / tot for k, v in papel.items()} if tot > 0 else {}

    ausentes = [c.nome for c in comps if not c.ok]
    return ResultadoEmpresa(empresa, fus, F, F2, ativos, s, lmax, log, ausentes, papel)
