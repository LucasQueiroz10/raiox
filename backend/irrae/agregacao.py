"""Look-through de ETFs: abrir a carteira e agregar o IrRAE de cada ação.

Exposição do ETF (em % do patrimônio) = soma, sobre as ações cobertas, de
    peso_i x IrRAE_i
mais um balde 'nao_coberto' (caixa, derivativos, ações ainda sem IrRAE).

Incerteza: o IrRAE de cada ação tem amostras. Como os erros de estimação das
ações podem ser correlacionados (mesmo método de mapeamento, mesmos kappa),
o intervalo do ETF é reportado em dois casos-limite:
  - independente: erros das ações independentes (intervalo mais estreito);
  - comonotônico: erros perfeitamente alinhados (intervalo mais largo). Para
    somas comonotônicas os quantis se somam: Q_ETF(p) = soma_i peso_i Q_i(p)
    (Dhaene et al. 2002). Entre todas as dependências possíveis com as mesmas
    marginais, a comonotônica maximiza a variância da soma.
A verdade fica entre os dois.

Circularidade: o componente E (Enquadramento) de cada ação usa as carteiras de
ETFs. Ao analisar um ETF, recalcule o E das ações SEM esse ETF
(posicoes_sem_etf), senão o rótulo do ETF confirma a si mesmo. Para auditar se
um "ETF de IA" é mesmo de IA, o mais limpo é desligar o E.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .taxonomia import Taxonomia

NAO_COBERTO = "nao_coberto"


def posicoes_sem_etf(
    posicoes_e: list[tuple[str, str, float]], etf_id: str
) -> list[tuple[str, str, float]]:
    """Remove o ETF analisado das posições usadas para montar o componente E de uma ação."""
    return [p for p in posicoes_e if p[0] != etf_id]


@dataclass
class ExposicaoETF:
    etf: str
    cobertura: float
    colunas: list[str]  # folhas + temas + 'nao_coberto'
    media: np.ndarray
    p05_indep: np.ndarray
    p95_indep: np.ndarray
    p05_comon: np.ndarray
    p95_comon: np.ndarray
    contribuicoes: pd.DataFrame  # por ação: peso, contribuição média por tema, parcela da variância

    def tabela(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "etf": self.etf,
                "area": self.colunas,
                "media": self.media,
                "p05_indep": self.p05_indep,
                "p95_indep": self.p95_indep,
                "p05_comon": self.p05_comon,
                "p95_comon": self.p95_comon,
                "cobertura": self.cobertura,
            }
        )


def _com_temas(x: np.ndarray, tax: Taxonomia) -> np.ndarray:
    """(S, L) -> (S, L + n_temas): acrescenta colunas com o total de cada tema."""
    temas = tax.agregar_temas(x)
    return np.column_stack([x] + [temas[t] for t in tax.temas])


def exposicao_etf(
    etf: str,
    pesos: dict[str, float],
    amostras: dict[str, np.ndarray],
    tax: Taxonomia,
    rng: np.random.Generator,
) -> ExposicaoETF:
    """pesos: ação -> fração do patrimônio do ETF (pctVal/100 do N-PORT); pode somar < 1.
    amostras: ação -> amostras (S, L) do IrRAE (após regras). Ações sem amostras = não cobertas."""
    cobertas = [a for a in pesos if a in amostras and pesos[a] > 0]
    cobertura = float(sum(pesos[a] for a in cobertas))
    colunas = list(tax.folhas) + list(tax.temas) + [NAO_COBERTO]
    if not cobertas:
        z = np.zeros(len(colunas))
        z[-1] = 1.0
        return ExposicaoETF(etf, 0.0, colunas, z, z, z, z, z, pd.DataFrame())
    S = min(amostras[a].shape[0] for a in cobertas)
    blocos = {a: _com_temas(amostras[a][:S], tax) for a in cobertas}
    w = np.array([pesos[a] for a in cobertas])

    # independente: cada ação com sua própria permutação das amostras
    indep = sum(wi * blocos[a][rng.permutation(S)] for wi, a in zip(w, cobertas, strict=True))
    # comonotônico: quantis somam
    qs = (0.05, 0.95)
    comon = {
        q: sum(wi * np.quantile(blocos[a], q, axis=0) for wi, a in zip(w, cobertas, strict=True))
        for q in qs
    }
    media = indep.mean(axis=0)

    resto = 1.0 - cobertura
    anexar = lambda v, r: np.append(v, r)  # noqa: E731
    contrib = []
    var_indep = sum((wi**2) * blocos[a].var(axis=0) for wi, a in zip(w, cobertas, strict=True))
    for wi, a in zip(w, cobertas, strict=True):
        linha = {"acao": a, "peso": wi}
        for j, t in enumerate(tax.temas):
            col = tax.L + j
            linha[f"contrib_{t}"] = wi * blocos[a][:, col].mean()
            linha[f"parcela_var_{t}"] = (
                (wi**2) * blocos[a][:, col].var() / max(var_indep[col], 1e-12)
            )
        contrib.append(linha)
    return ExposicaoETF(
        etf,
        cobertura,
        colunas,
        anexar(media, resto),
        anexar(np.quantile(indep, 0.05, axis=0), resto),
        anexar(np.quantile(indep, 0.95, axis=0), resto),
        anexar(comon[0.05], resto),
        anexar(comon[0.95], resto),
        pd.DataFrame(contrib).sort_values("peso", ascending=False),
    )


def pesos_da_carteira(
    carteira: pd.DataFrame, mapa_id_acao: dict[str, str], campo: str = "cusip"
) -> dict[str, float]:
    """N-PORT (saída de ingest.nport.parse_nport) -> {ação: fração do patrimônio}.
    Posições que não são ações mapeadas (caixa, derivativos, ações fora do universo) ficam de fora
    e aparecem como 'nao_coberto' na agregação."""
    df = carteira[carteira["payoffProfile"].fillna("Long") == "Long"]
    out: dict[str, float] = {}
    for _, r in df.iterrows():
        acao = mapa_id_acao.get(r[campo])
        if acao:
            out[acao] = out.get(acao, 0.0) + float(r["pctVal"]) / 100.0
    return out
