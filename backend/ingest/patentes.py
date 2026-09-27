"""Patentes -> componente R (Pesquisa).

Fontes públicas:
  - USPTO Artificial Intelligence Patent Dataset (AIPD, atualização 2023): para cada documento
    (patente ou publicação de pedido), previsões de IA em 8 componentes:
    ml, ec, nlp, vision, speech, kp, pc, hw. Colunas: doc_id, flag_patent, pub_dt, appl_id,
    predict50_* / predict86_* / predict93_*, ai_score_*.
  - PatentsView (desde 20/03/2026 no USPTO Open Data Portal): tabela de titulares
    (assignees) desambiguados para ligar patente -> empresa.
NÃO executado no protótipo (hosts bloqueados no sandbox); testado com fixtures.

Ligar titular -> empresa (CIK) é o passo mais trabalhoso: exige tabela de nomes
(e subsidiárias) curada. Comece pelas empresas do tema e revise manualmente.
"""

from __future__ import annotations

import pandas as pd

# componentes do AIPD -> folhas da taxonomia (ajuste conforme a taxonomia crescer)
MAPA_AIPD_FOLHA = {
    "hw": "ia.semicondutores",
    "ml": "ia.modelos_software",
    "nlp": "ia.modelos_software",
    "speech": "ia.modelos_software",
    "vision": "ia.modelos_software",
    "kp": "ia.modelos_software",
    "pc": "ia.modelos_software",
    "ec": "ia.modelos_software",
}


def contagens_por_empresa(
    aipd: pd.DataFrame,
    titulares: pd.DataFrame,
    mapa_titular_empresa: dict[str, str],
    inicio: str,
    fim: str,
    limiar: str = "predict50",
    mapa_folha: dict[str, str] | None = None,
    col_patente: str = "patent_id",
    col_titular: str = "disambig_assignee_organization",
) -> dict[str, tuple[dict, int]]:
    """Retorna empresa -> ({folha: contagem}, total de patentes na janela).

    Cada patente de IA é repartida igualmente entre os componentes de IA que o modelo marcou
    (evita contar a mesma patente várias vezes). Patentes sem IA contam só no total (-> núcleo).
    Use janela pela data de depósito quando disponível; aqui usa pub_dt (simplificação).
    """
    mapa_folha = mapa_folha or MAPA_AIPD_FOLHA
    a = aipd[
        (aipd["flag_patent"] == 1) & (aipd["pub_dt"] >= inicio) & (aipd["pub_dt"] <= fim)
    ].copy()
    a[col_patente] = a["doc_id"].astype(str)
    t = titulares[[col_patente, col_titular]].copy()
    t[col_patente] = t[col_patente].astype(str)
    t["empresa"] = t[col_titular].map(mapa_titular_empresa)
    t = t.dropna(subset=["empresa"]).drop_duplicates([col_patente, "empresa"])
    m = a.merge(t[[col_patente, "empresa"]], on=col_patente)
    comps = [c for c in mapa_folha if f"{limiar}_{c}" in m.columns]
    out = {}
    for emp, g in m.groupby("empresa"):
        cont: dict[str, float] = {}
        flags = g[[f"{limiar}_{c}" for c in comps]].to_numpy()
        n_flags = flags.sum(axis=1)
        for j, c in enumerate(comps):
            peso = (flags[:, j] / pd.Series(n_flags).replace(0, 1).to_numpy()).sum()
            if peso > 0:
                cont[mapa_folha[c]] = cont.get(mapa_folha[c], 0.0) + float(peso)
        out[emp] = (cont, int(len(g)))
    return out
