"""Snapshots de exemplo da vitrine, enquanto não há cálculo com dados reais (ADR 0009).

Uso (de dentro de backend/): python -m vitrine.exemplo
Grava ../frontend/src/dados_exemplo/{big-techs,sp500,ibovespa}.json. Um teste confere que os
arquivos commitados batem com este gerador.

Decisão do Lucas (11/11/2026): empresas reais, com pesos em % e exposição inventados; nada em
reais. Por isso:
- todo snapshot sai com ilustrativo = true, e o site mostra a faixa "Números ilustrativos";
- os números são sorteados com semente fixa, não ajustados à mão, para não parecerem um
  julgamento sobre cada empresa;
- nenhuma fonte é citada: composição e exposição inventadas não podem creditar o CDA nem o N-PORT.
Os CNPJs e os setores das empresas brasileiras vêm do cadastro da CVM (FCA) carregado no banco
local em 11/11/2026, não digitados de memória. As americanas usam "US:" + ticker (DT-3).
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

from vitrine.snapshot import (
    COMPONENTE_PRIOR,
    COMPONENTES,
    MIN_COMPONENTES_REAIS,
    SELO_LARGURA_ALTA,
    SELO_LARGURA_MEDIA,
    TAXONOMIA,
    Snapshot,
)

PASTA_PADRAO = Path(__file__).resolve().parents[2] / "frontend" / "src" / "dados_exemplo"
SEMENTE_PADRAO = 20261111
CASAS = Decimal("0.000001")
TEMA = "ia"

# (ticker, nome, empresa_id, setor). Setores das brasileiras: setor de atividade do FCA.
# Setores das americanas: rótulos próprios (a vitrine não usa GICS).
BIG_TECHS = [
    ("NVDA", "NVIDIA", "US:NVDA", "Semicondutores"),
    ("AMZN", "Amazon", "US:AMZN", "Comércio eletrônico e nuvem"),
    ("AAPL", "Apple", "US:AAPL", "Hardware de consumo"),
    ("MSFT", "Microsoft", "US:MSFT", "Software"),
]
SP500 = BIG_TECHS + [
    ("GOOGL", "Alphabet", "US:GOOGL", "Internet e publicidade"),
    ("META", "Meta Platforms", "US:META", "Internet e publicidade"),
    ("AVGO", "Broadcom", "US:AVGO", "Semicondutores"),
    ("TSLA", "Tesla", "US:TSLA", "Veículos"),
    ("BRK.B", "Berkshire Hathaway", "US:BRK.B", "Conglomerado financeiro"),
    ("JPM", "JPMorgan Chase", "US:JPM", "Bancos"),
    ("LLY", "Eli Lilly", "US:LLY", "Farmacêutico"),
    ("V", "Visa", "US:V", "Meios de pagamento"),
    ("XOM", "Exxon Mobil", "US:XOM", "Petróleo e gás"),
    ("MA", "Mastercard", "US:MA", "Meios de pagamento"),
    ("UNH", "UnitedHealth", "US:UNH", "Saúde"),
    ("JNJ", "Johnson & Johnson", "US:JNJ", "Farmacêutico"),
    ("PG", "Procter & Gamble", "US:PG", "Bens de consumo"),
    ("HD", "Home Depot", "US:HD", "Varejo"),
    ("COST", "Costco", "US:COST", "Varejo"),
    ("ORCL", "Oracle", "US:ORCL", "Software"),
    ("WMT", "Walmart", "US:WMT", "Varejo"),
    ("NFLX", "Netflix", "US:NFLX", "Mídia e entretenimento"),
    ("AMD", "AMD", "US:AMD", "Semicondutores"),
    ("CRM", "Salesforce", "US:CRM", "Software"),
    ("KO", "Coca-Cola", "US:KO", "Bebidas"),
    ("PEP", "PepsiCo", "US:PEP", "Bebidas"),
    ("BAC", "Bank of America", "US:BAC", "Bancos"),
    ("ADBE", "Adobe", "US:ADBE", "Software"),
    ("CSCO", "Cisco", "US:CSCO", "Equipamentos de rede"),
    ("INTC", "Intel", "US:INTC", "Semicondutores"),
]
IBOVESPA = [
    ("PETR4", "Petrobras", "BR:CNPJ:33000167000101", "Petróleo e Gás"),
    ("VALE3", "Vale", "BR:CNPJ:33592510000154", "Extração Mineral"),
    ("ITUB4", "Itaú Unibanco", "BR:CNPJ:60872504000123", "Bancos"),
    ("BBDC4", "Bradesco", "BR:CNPJ:60746948000112", "Bancos"),
    ("B3SA3", "B3", "BR:CNPJ:09346601000125", "Bolsas de Valores/Mercadorias e Futuros"),
    ("ABEV3", "Ambev", "BR:CNPJ:07526557000100", "Bebidas e Fumo"),
    ("WEGE3", "WEG", "BR:CNPJ:84429695000111", "Emp. Adm. Part. - Máqs., Equip., Veíc. e Peças"),
    ("BBAS3", "Banco do Brasil", "BR:CNPJ:00000000000191", "Bancos"),
    ("ITSA4", "Itaúsa", "BR:CNPJ:61532644000115", "Emp. Adm. Part. - Intermediação Financeira"),
    ("BPAC11", "BTG Pactual", "BR:CNPJ:30306294000145", "Bancos"),
    ("SUZB3", "Suzano", "BR:CNPJ:16404287000155", "Papel e Celulose"),
    ("GGBR4", "Gerdau", "BR:CNPJ:33611500000119", "Metalurgia e Siderurgia"),
    ("RENT3", "Localiza", "BR:CNPJ:16670085000155", "Serviços Transporte e Logística"),
    ("RDOR3", "Rede D'Or", "BR:CNPJ:06047087000139", "Serviços médicos"),
    ("EQTL3", "Equatorial", "BR:CNPJ:03220438000173", "Energia Elétrica"),
    ("EMBJ3", "Embraer", "BR:CNPJ:07689002000189", "Máquinas, Equipamentos, Veículos e Peças"),
    ("TOTS3", "Totvs", "BR:CNPJ:53113791000122", "Comunicação e Informática"),
    ("SBSP3", "Sabesp", "BR:CNPJ:43776517000180", "Saneamento, Serv. Água e Gás"),
    ("PRIO3", "PRIO", "BR:CNPJ:10629105000168", "Petróleo e Gás"),
    ("RADL3", "Raia Drogasil", "BR:CNPJ:61585865000151", "Comércio (Atacado e Varejo)"),
    ("VIVT3", "Vivo", "BR:CNPJ:02558157000162", "Telecomunicações"),
    ("CMIG4", "Cemig", "BR:CNPJ:17155730000164", "Energia Elétrica"),
    ("LREN3", "Lojas Renner", "BR:CNPJ:92754738000162", "Comércio (Atacado e Varejo)"),
    ("UGPA3", "Ultrapar", "BR:CNPJ:33256439000139", "Emp. Adm. Part. - Petróleo e Gás"),
    ("CSAN3", "Cosan", "BR:CNPJ:50746577000115", "Agricultura (Açúcar, Álcool e Cana)"),
    ("HAPV3", "Hapvida", "BR:CNPJ:05197443000138", "Serviços médicos"),
    ("KLBN11", "Klabin", "BR:CNPJ:89637490000145", "Papel e Celulose"),
]

# Textos das carteiras: os mesmos de docs/textos_telas.md (seção Vitrine > Carteiras).
CARTEIRAS = {
    "big-techs": (
        "4 big techs americanas",
        "NVIDIA, Amazon, Apple e Microsoft, 25% cada.",
    ),
    "sp500": (
        "S&P 500",
        "Um ETF que replica o índice (IVV), aberto pela carteira que ele declara à SEC.",
    ),
    "ibovespa": (
        "Ibovespa",
        "Um ETF que replica o índice (BOVA11), aberto pela carteira que ele informa à CVM.",
    ),
}
DATA_REFERENCIA = date(2026, 9, 30)
GERADO_EM = datetime.fromisoformat("2026-11-11T00:00:00+00:00")
CAIXA_DO_ETF = Decimal("0.005")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(CASAS, rounding=ROUND_HALF_EVEN)


def _d(valor: float) -> Decimal:
    return _q(Decimal(str(valor)))


def _partes_que_somam(rng: random.Random, n: int, total: Decimal) -> list[Decimal]:
    """n frações sorteadas que somam exatamente o total, já arredondadas."""
    brutos = [rng.random() ** 2 + 0.05 for _ in range(n)]
    soma = sum(brutos)
    partes = [_q(total * Decimal(str(b / soma))) for b in brutos]
    partes[-1] += total - sum(partes)
    return partes


def _faixa(rng: random.Random, media: Decimal, meia_largura: float) -> tuple[Decimal, Decimal]:
    p5 = max(Decimal(0), media - _d(rng.uniform(0.2, 1) * meia_largura))
    p95 = min(Decimal(1), media + _d(rng.uniform(0.2, 1) * meia_largura))
    return p5, p95


def _componentes(rng: random.Random, so_prior: bool) -> list[dict]:
    if so_prior:
        presentes = [COMPONENTE_PRIOR]
    else:
        reais = [c for c in COMPONENTES if c != COMPONENTE_PRIOR]
        presentes = rng.sample(reais, rng.randint(1, len(reais)))
        if rng.random() < 0.6:
            presentes.append(COMPONENTE_PRIOR)
    pesos = dict(zip(presentes, _partes_que_somam(rng, len(presentes), Decimal(1)), strict=True))
    return [
        {"id": c, "nome": nome, "peso_p": pesos.get(c, Decimal(0)), "presente": c in pesos}
        for c, nome in COMPONENTES.items()
    ]


def _selo(media_faixa: list[tuple[Decimal, Decimal]], componentes: list[dict], so_prior: bool):
    # Mesma regra do modelo (vitrine/snapshot.py, que segue irrae/regras.py).

    if so_prior:
        return "preliminar"
    reais = sum(1 for c in componentes if c["presente"] and c["id"] != COMPONENTE_PRIOR)
    maior = max(p95 - p5 for p5, p95 in media_faixa)
    if reais < MIN_COMPONENTES_REAIS:
        return "preliminar"
    if maior < SELO_LARGURA_ALTA:
        return "alta"
    if maior < SELO_LARGURA_MEDIA:
        return "media"
    return "preliminar"


def _irrae(rng: random.Random, origem: str) -> dict:
    if origem == "nao_coberto":
        return {"origem": "nao_coberto"}
    folhas_tema = TAXONOMIA[TEMA]["folhas"]
    so_prior = origem == "so_prior"
    if so_prior:
        # Só o prior do setor: tudo na folha genérica, com faixa larga.
        escolhidas = [f"{TEMA}.generica"]
        media = _d(rng.uniform(0, 0.15))
        medias = [media]
    else:
        especificas = [f for f in folhas_tema if f != f"{TEMA}.generica"]
        escolhidas = rng.sample(especificas, rng.randint(1, 3))
        media = _d(rng.random() ** 1.6 * 0.9)
        medias = _partes_que_somam(rng, len(escolhidas), media)
    folhas = []
    for id_folha, media_folha in zip(escolhidas, medias, strict=True):
        p5, p95 = _faixa(rng, media_folha, 0.18 if so_prior else 0.07)
        folhas.append(
            {
                "id": id_folha,
                "nome": folhas_tema[id_folha],
                "media": media_folha,
                "p5": p5,
                "p95": p95,
            }
        )
    p5, p95 = _faixa(rng, media, 0.2 if so_prior else 0.09)
    componentes = _componentes(rng, so_prior)
    faixas = [(p5, p95)] + [(f["p5"], f["p95"]) for f in folhas]
    return {
        "origem": origem,
        "tema": TEMA,
        "media": media,
        "p5": p5,
        "p95": p95,
        "selo": _selo(faixas, componentes, so_prior),
        "folhas": folhas,
        "componentes": componentes,
    }


def _origem(rng: random.Random) -> str:
    sorteio = rng.random()
    return "irrae" if sorteio < 0.75 else ("so_prior" if sorteio < 0.9 else "nao_coberto")


def _exposicao(empresas: list[dict]) -> tuple[dict, dict]:
    cobertas = [e for e in empresas if e["irrae"]["origem"] != "nao_coberto"]
    folhas_tema = TAXONOMIA[TEMA]["folhas"]

    def soma(campo: str, folha: str | None = None) -> Decimal:
        total = Decimal(0)
        for e in cobertas:
            if folha is None:
                total += e["peso_efetivo"] * e["irrae"][campo]
            else:
                total += sum(
                    (
                        e["peso_efetivo"] * f[campo]
                        for f in e["irrae"]["folhas"]
                        if f["id"] == folha
                    ),
                    Decimal(0),
                )
        return _q(total)

    tema = {
        "id": TEMA,
        "nome": TAXONOMIA[TEMA]["nome"],
        "media": soma("media"),
        "p5": soma("p5"),
        "p95": soma("p95"),
        "subtemas": [
            {
                "id": f,
                "nome": nome,
                "media": soma("media", f),
                "p5": soma("p5", f),
                "p95": soma("p95", f),
            }
            for f, nome in folhas_tema.items()
        ],
    }
    coberto = sum((e["peso_efetivo"] for e in cobertas), Decimal(0))
    nao_coberto = 1 - coberto
    setores: dict[str, Decimal] = {}
    for e in empresas:
        setores[e["setor"]] = setores.get(e["setor"], Decimal(0)) + e["peso_efetivo"]
    resto = 1 - sum(setores.values(), Decimal(0))
    lista_setores = [
        {"id": s, "nome": s, "peso": p} for s, p in sorted(setores.items(), key=lambda x: -x[1])
    ]
    if resto > 0:
        lista_setores.append(
            {"id": "caixa_e_outros", "nome": "Caixa e outros ativos", "peso": resto}
        )
    exposicao = {
        "setores": lista_setores,
        "temas": [tema],
        "fora_do_tema": 1 - tema["media"] - nao_coberto,
        "nao_coberto": nao_coberto,
    }
    cobertura = {
        "peso_com_irrae": sum(
            (e["peso_efetivo"] for e in cobertas if e["irrae"]["origem"] == "irrae"), Decimal(0)
        ),
        "peso_so_prior": sum(
            (e["peso_efetivo"] for e in cobertas if e["irrae"]["origem"] == "so_prior"), Decimal(0)
        ),
        "peso_nao_coberto": nao_coberto,
    }
    return exposicao, cobertura


def _snapshot(
    rng: random.Random, id_carteira: str, lista: list[tuple], etf: str | None
) -> Snapshot:
    if etf is None:
        pesos = [Decimal(1) / len(lista)] * len(lista)
        posicoes = [
            {"ticker": t, "nome": nome, "tipo": "acao", "peso": p}
            for (t, nome, _, _), p in zip(lista, pesos, strict=True)
        ]
        origens = ["irrae"] * len(lista)
        caminho: list[str] = []
    else:
        pesos = sorted(_partes_que_somam(rng, len(lista), 1 - CAIXA_DO_ETF), reverse=True)
        posicoes = [{"ticker": etf, "nome": etf, "tipo": "etf", "peso": Decimal(1)}]
        # Garante as três origens em todo ETF, para o site exercitar os três estados.
        origens = ["irrae", "so_prior", "nao_coberto"] + [_origem(rng) for _ in lista[3:]]
        rng.shuffle(origens)
        caminho = [etf]
    empresas = [
        {
            "empresa_id": empresa_id,
            "ticker": ticker,
            "nome": nome,
            "pais": "BR" if empresa_id.startswith("BR:") else "US",
            "peso_efetivo": peso,
            "caminho": caminho,
            "setor": setor,
            "irrae": _irrae(rng, origem),
            "fontes": [],
        }
        for (ticker, nome, empresa_id, setor), peso, origem in zip(
            lista, pesos, origens, strict=True
        )
    ]
    exposicao, cobertura = _exposicao(empresas)
    nome, descricao = CARTEIRAS[id_carteira]
    return Snapshot.model_validate(
        {
            "versao_schema": "1",
            "ilustrativo": True,
            "carteira": {
                "id": id_carteira,
                "nome": nome,
                "descricao": descricao,
                "data_referencia": DATA_REFERENCIA,
                "posicoes": posicoes,
            },
            "modelo": {
                "versao_irrae": "1.1",
                "n_amostras": 2000,
                "semente": 0,
                "gerado_em": GERADO_EM,
                "cenario_faixa_carteira": "comonotonico",
            },
            "cobertura": cobertura,
            "exposicao": exposicao,
            "empresas": empresas,
            "fontes_carteira": [],
        }
    )


def gerar(semente: int = SEMENTE_PADRAO) -> list[Snapshot]:
    rng = random.Random(semente)  # noqa: S311 - números ilustrativos, não segurança
    return [
        _snapshot(rng, "big-techs", BIG_TECHS, None),
        _snapshot(rng, "sp500", SP500, "IVV"),
        _snapshot(rng, "ibovespa", IBOVESPA, "BOVA11"),
    ]


def texto_json(snapshot: Snapshot) -> str:
    return json.dumps(snapshot.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"


def gravar(pasta: Path = PASTA_PADRAO) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    for snapshot in gerar():
        destino = pasta / f"{snapshot.carteira.id}.json"
        destino.write_text(texto_json(snapshot), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    gravar(Path(sys.argv[1]) if len(sys.argv) > 1 else PASTA_PADRAO)
