"""Parsers de bases públicas testados com arquivos mínimos (a rede está bloqueada no protótipo)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from ingest.narrativa import (
    componente_narrativa_contagens,
    escore_ameaca,
    extrair_texto,
    secoes_10k,
)
from ingest.nport import parse_nport, posicoes_empresa
from ingest.patentes import contagens_por_empresa
from ingest.sec_edgar import parse_segmentos_instancia, segmentos_fsn

FIX = Path(__file__).resolve().parents[1] / "fixtures"
CONFIG_IRRAE = Path(__file__).resolve().parents[2] / "irrae" / "config"


def test_xbrl_segmentos_anuais_e_unidimensionais():
    df = parse_segmentos_instancia((FIX / "xbrl_min.xml").read_bytes())
    rec = df[df.metrica == "receita"].set_index("segmento").valor
    # usa a tag de maior prioridade (Revenues) quando há duas;
    # ignora trimestre e contexto com 2 dimensões
    assert rec["NuvemSegmentMember"] == pytest.approx(30500)
    assert rec["VarejoSegmentMember"] == pytest.approx(70000)
    assert len(rec) == 2
    lucro = df[df.metrica == "lucro_op"].set_index("segmento").valor
    assert lucro["VarejoSegmentMember"] == pytest.approx(-1000)


def test_fsn_segmentos():
    sub = pd.DataFrame({"adsh": ["a1"], "cik": [1], "form": ["10-K"]})
    dim = pd.DataFrame(
        {
            "dimh": ["h1", "h2", "h3"],
            "segments": [
                "BusinessSegments=Nuvem;",
                "BusinessSegments=Nuvem;ProductOrService=X;",
                None,
            ],
        }
    )
    num = pd.DataFrame(
        {
            "adsh": ["a1"] * 3,
            "tag": ["Revenues"] * 3,
            "qtrs": [4, 4, 4],
            "ddate": [20251231] * 3,
            "dimh": ["h1", "h2", "h3"],
            "value": [3e10, 1e9, 1e11],
        }
    )
    out = segmentos_fsn(num, dim, sub, cik=1)
    assert list(out.segmento) == ["Nuvem"] and out.valor.iloc[0] == pytest.approx(30000)


def test_nport():
    info, pos = parse_nport((FIX / "nport_min.xml").read_bytes())
    assert info["seriesId"] == "S000000001" and len(pos) == 2
    p = posicoes_empresa(
        {"S000000001": pos}, {"S000000001": "ia.modelos_software"}, {"cusip": "000000AA1"}
    )
    assert p == [("S000000001", "ia.modelos_software", 50_000_000.0)]


def test_narrativa_secoes_contagens_e_ameaca():
    html = (FIX / "tenk_min.html").read_text(encoding="utf-8")
    sec = secoes_10k(extrair_texto(html))
    assert (
        "retail stores" in sec["1"]
        and "disrupt" in sec["1a"]
        and "Capital expenditures" in sec["7"]
    )
    dic = json.loads((CONFIG_IRRAE / "dicionario_narrativa.json").read_text(encoding="utf-8"))
    cont, total = componente_narrativa_contagens(html, dic["folhas"])
    assert total >= 6
    assert (
        cont["ia.nuvem_dc"] > 0
        and cont["ia.semicondutores"] > 0
        and cont.get("ia.generica", 0) >= 1
    )
    s, n = escore_ameaca(sec["1a"], dic["termos_ia"], dic["termos_ameaca"])
    assert n == 2 and s == pytest.approx(-0.5)


def test_patentes_contagens():
    aipd = pd.read_csv(FIX / "aipd_min.csv", dtype={"doc_id": str})
    tit = pd.read_csv(FIX / "assignee_min.tsv", sep="\t", dtype={"patent_id": str})
    out = contagens_por_empresa(
        aipd, tit, {"ALFA CORP": "ALFA", "BETA INC": "BETA"}, "2023-01-01", "2025-12-31"
    )
    cont, total = out["ALFA"]
    # 3 patentes na janela: uma ml+nlp (-> modelos), uma hw (-> semis), uma sem IA;
    # a de 2019 fica fora
    assert total == 3
    assert cont == {"ia.modelos_software": 1.0, "ia.semicondutores": 1.0}
    assert out["BETA"] == ({}, 1)  # tem patente, nenhuma de IA: zero, não ausente
