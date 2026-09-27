"""Ingestão de dados da SEC (EDGAR). NÃO executado no ambiente do protótipo
(o sandbox bloqueia sec.gov); testado com fixtures em tests/fixtures.

Regras da SEC (Accessing EDGAR Data): declarar User-Agent "Nome email@dominio"
e no máximo 10 requisições/segundo.

Três caminhos para dados por SEGMENTO (as APIs XBRL do data.sec.gov NÃO trazem
dados dimensionais/segmentos, só fatos da entidade inteira):
  1. Instância XBRL de um 10-K (arquivo *_htm.xml na pasta do filing) -> parse_segmentos_instancia
  2. Financial Statement and Notes Data Sets (mensal, com dimensões) -> segmentos_fsn   [escala]
  3. APIs data.sec.gov para fatos não-dimensionais (RPO, capex total, SIC) -> ClienteEDGAR
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd
from lxml import etree

NS_XBRLI = "http://www.xbrl.org/2003/instance"
NS_XBRLDI = "http://xbrl.org/2006/xbrldi"

TAGS_PADRAO = {
    "receita": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
    ],
    "lucro_op": ["OperatingIncomeLoss"],
    "capex_segmento": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "SegmentExpenditureAdditionToLongLivedAssets",
    ],
}
EIXO_SEGMENTO = "StatementBusinessSegmentsAxis"


@dataclass
class ClienteEDGAR:
    user_agent: str  # ex.: "IrRAE pesquisa contato@seudominio.com"
    max_rps: float = 8.0  # abaixo do limite de 10/s da SEC
    _ultimo: float = 0.0

    def _get(self, url: str) -> bytes:
        import requests

        espera = 1.0 / self.max_rps - (time.time() - self._ultimo)
        if espera > 0:
            time.sleep(espera)
        r = requests.get(
            url,
            headers={"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"},
            timeout=60,
        )
        self._ultimo = time.time()
        r.raise_for_status()
        return r.content

    def json(self, url: str) -> dict:
        import json

        return json.loads(self._get(url))

    def submissions(self, cik: str | int) -> dict:
        return self.json(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")

    def companyconcept(self, cik: str | int, tag: str, taxonomia: str = "us-gaap") -> dict:
        return self.json(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{int(cik):010d}/{taxonomia}/{tag}.json"
        )

    def ultimo_10k(self, cik: str | int) -> dict:
        """Último 10-K: accession, data, documento principal e URL da instância XBRL extraída."""
        rec = self.submissions(cik)["filings"]["recent"]
        for i, f in enumerate(rec["form"]):
            if f == "10-K":
                acc = rec["accessionNumber"][i]
                doc = rec["primaryDocument"][i]
                base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}"
                return {
                    "accession": acc,
                    "data": rec["filingDate"][i],
                    "periodo": rec["reportDate"][i],
                    "documento": f"{base}/{doc}",
                    "instancia": f"{base}/{doc.replace('.htm', '_htm.xml')}",
                }
        raise LookupError("nenhum 10-K em filings.recent")

    def valor_mais_recente(self, cik: str | int, tag: str, forma: str = "10-K") -> dict | None:
        """Ex.: RevenueRemainingPerformanceObligation (RPO) -> último valor reportado num 10-K."""
        dados = self.companyconcept(cik, tag)
        vals = [v for unid in dados["units"].values() for v in unid if v.get("form") == forma]
        return max(vals, key=lambda v: (v["end"], v["filed"])) if vals else None


def parse_segmentos_instancia(
    xml: bytes,
    tags: dict[str, list[str]] | None = None,
    eixo: str = EIXO_SEGMENTO,
    dias_min: int = 350,
) -> pd.DataFrame:
    """Extrai fatos anuais por segmento de uma instância XBRL.

    Mantém só contextos com UMA dimensão (o eixo de segmentos) e duração ~1 ano,
    para não somar duas vezes cortes por produto/região.
    Retorna: segmento, metrica, tag, valor, inicio, fim.
    """
    tags = tags or TAGS_PADRAO
    raiz = etree.fromstring(xml)
    ctx = {}
    for c in raiz.iter(f"{{{NS_XBRLI}}}context"):
        membros = c.findall(f".//{{{NS_XBRLDI}}}explicitMember")
        if len(membros) != 1 or not membros[0].get("dimension", "").endswith(eixo):
            continue
        ini, fim = c.find(f".//{{{NS_XBRLI}}}startDate"), c.find(f".//{{{NS_XBRLI}}}endDate")
        if ini is None or fim is None:
            continue
        d0, d1 = pd.Timestamp(ini.text), pd.Timestamp(fim.text)
        if (d1 - d0).days < dias_min:
            continue
        membro = membros[0].text.strip().split(":")[-1]
        ctx[c.get("id")] = (membro, d0.date(), d1.date())
    tag_para_metrica = {t: m for m, lst in tags.items() for t in lst}
    linhas = []
    for el in raiz.iter():
        if not isinstance(el.tag, str) or "}" not in el.tag:
            continue
        local = el.tag.split("}")[1]
        if local in tag_para_metrica and el.get("contextRef") in ctx and el.text:
            seg, d0, d1 = ctx[el.get("contextRef")]
            linhas.append(
                {
                    "segmento": seg,
                    "metrica": tag_para_metrica[local],
                    "tag": local,
                    "valor": float(el.text) / 1e6,
                    "inicio": d0,
                    "fim": d1,
                }
            )
    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    # se a mesma métrica vier em mais de uma tag, fica a primeira da lista de prioridade
    prio = {t: i for m, lst in tags.items() for i, t in enumerate(lst)}
    df["prio"] = df["tag"].map(prio)
    df = df.sort_values("prio").drop_duplicates(["segmento", "metrica", "fim"]).drop(columns="prio")
    return df.sort_values(["metrica", "segmento"]).reset_index(drop=True)


def segmentos_fsn(
    num: pd.DataFrame,
    dim: pd.DataFrame,
    sub: pd.DataFrame,
    cik: int,
    tags: dict[str, list[str]] | None = None,
    eixo_curto: str = "BusinessSegments",
) -> pd.DataFrame:
    """Mesmo resultado a partir dos Financial Statement and Notes Data Sets (num/dim/sub .tsv).

    Na tabela DIM, 'segments' vem como "{eixo}={membro};" com prefixos/sufixos comuns removidos
    (ex.: StatementBusinessSegmentsAxis -> BusinessSegments). Verifique o formato exato no
    arquivo real antes de rodar em escala.
    """
    tags = tags or TAGS_PADRAO
    tag_para_metrica = {t: m for m, lst in tags.items() for t in lst}
    adsh = sub.loc[(sub["cik"].astype(int) == int(cik)) & (sub["form"] == "10-K"), "adsh"]
    d = dim[dim["segments"].fillna("").str.fullmatch(rf"{eixo_curto}=[^;]+;")].copy()
    d["segmento"] = d["segments"].str.extract(rf"{eixo_curto}=([^;]+);")[0]
    n = num[num["adsh"].isin(adsh) & (num["qtrs"] == 4) & num["tag"].isin(tag_para_metrica)]
    n = n.merge(d[["dimh", "segmento"]], on="dimh")
    n["metrica"] = n["tag"].map(tag_para_metrica)
    n["valor"] = n["value"].astype(float) / 1e6
    return n[["adsh", "segmento", "metrica", "tag", "ddate", "valor"]].reset_index(drop=True)
