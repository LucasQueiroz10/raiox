"""Carteiras de ETFs pelo Form N-PORT (SEC). Dois usos: (1) look-through do ETF (abrir a carteira e
agregar o IrRAE das ações: agregacao.pesos_da_carteira + agregacao.exposicao_etf) e (2) componente E
(Enquadramento de mercado) de cada ação.

NÃO executado no ambiente do protótipo (sec.gov bloqueado); testado com fixture.
Estrutura XML conferida num NPORT-P real (namespace http://www.sec.gov/edgar/nport).
Atenção: carteiras públicas saem trimestralmente com ~60 dias de defasagem
(proposta da SEC de fev/2026 mantém esse regime), então E sempre chega atrasado.

Para escala, a SEC publica também os "Form N-PORT Data Sets" em lote.
"""

from __future__ import annotations

import pandas as pd

from ingest.xml_seguro import ler_xml

NS = {"n": "http://www.sec.gov/edgar/nport"}


def parse_nport(xml: bytes) -> tuple[dict, pd.DataFrame]:
    raiz = ler_xml(xml)

    def txt(caminho: str) -> str | None:
        el = raiz.find(caminho, NS)
        return el.text.strip() if el is not None and el.text else None

    info = {
        "seriesId": txt(".//n:genInfo/n:seriesId"),
        "seriesName": txt(".//n:genInfo/n:seriesName"),
        "repPdDate": txt(".//n:genInfo/n:repPdDate"),
        "netAssets": float(txt(".//n:fundInfo/n:netAssets") or "nan"),
    }
    linhas = []
    for inv in raiz.iterfind(".//n:invstOrSecs/n:invstOrSec", NS):

        def f(tag: str) -> str | None:
            el = inv.find(f"n:{tag}", NS)  # noqa: B023 - usado na mesma iteração
            return el.text.strip() if el is not None and el.text else None

        isin = inv.find("n:identifiers/n:isin", NS)
        linhas.append(
            {
                "name": f("name"),
                "lei": f("lei"),
                "cusip": f("cusip"),
                "isin": isin.get("value") if isin is not None else None,
                "valUSD": float(f("valUSD") or 0),
                "pctVal": float(f("pctVal") or 0),
                "assetCat": f("assetCat"),
                "payoffProfile": f("payoffProfile"),
            }
        )
    return info, pd.DataFrame(linhas)


def posicoes_empresa(
    carteiras: dict[str, pd.DataFrame],
    mapa_etf_folha: dict[str, str],
    identificador: dict[str, str],
) -> list[tuple[str, str, float]]:
    """Dólares da empresa em cada ETF mapeado.

    carteiras: seriesId -> DataFrame de parse_nport; mapa_etf_folha: seriesId -> folha ou 'nucleo'
    (ETFs amplos/setoriais vão para 'nucleo');
    identificador: {'cusip': ...} ou {'isin': ...} ou {'lei': ...}.
    Saída no formato de componentes.de_etfs.
    """
    ((campo, valor),) = identificador.items()
    out = []
    for sid, df in carteiras.items():
        if sid not in mapa_etf_folha:
            continue
        v = df.loc[
            (df[campo] == valor) & (df["payoffProfile"].fillna("Long") == "Long"), "valUSD"
        ].sum()
        if v > 0:
            out.append((sid, mapa_etf_folha[sid], float(v)))
    return out
