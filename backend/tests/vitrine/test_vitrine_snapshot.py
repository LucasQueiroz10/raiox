"""Contrato do snapshot da vitrine (ADR 0009, especificação da vitrine, seção 4).

Um snapshot sintético mínimo e válido, e uma mutação por regra que o modelo precisa recusar.
Os números fecham à mão: carteira com 60% na empresa A (coberta pelo IrRAE), 30% na B (não
coberta) e 10% em caixa.
"""

import copy
from decimal import Decimal

import pytest
from pydantic import ValidationError

from vitrine.snapshot import Snapshot

COMPONENTES = [
    "A_receita",
    "A_lucro",
    "C_cadeia",
    "Ir_capex",
    "B_backlog",
    "R_patentes",
    "P_participacoes",
    "N_narrativa",
    "prior_setorial",
]
NOMES_COMPONENTES = {
    "A_receita": "Atividade: receita por segmento",
    "A_lucro": "Atividade: lucro operacional por segmento",
    "C_cadeia": "Cadeia: exposição herdada de clientes",
    "Ir_capex": "Investimento recente: capex",
    "B_backlog": "Carteira contratada (RPO/backlog)",
    "R_patentes": "Pesquisa: patentes (USPTO AIPD)",
    "P_participacoes": "Participações e aquisições",
    "N_narrativa": "Narrativa: texto do 10-K",
    "prior_setorial": "Prior do setor oficial (pseudo-componente)",
}


def _componentes(presentes: dict[str, float]) -> list[dict]:
    return [
        {
            "id": c,
            "nome": NOMES_COMPONENTES[c],
            "peso_p": presentes.get(c, 0.0),
            "presente": c in presentes,
        }
        for c in COMPONENTES
    ]


def _subtema(id_: str, nome: str, media: float, p5: float, p95: float) -> dict:
    return {"id": id_, "nome": nome, "media": media, "p5": p5, "p95": p95}


def snapshot_valido() -> dict:
    return {
        "versao_schema": "1",
        "ilustrativo": True,
        "carteira": {
            "id": "sp500",
            "nome": "Carteira de teste",
            "descricao": "Um ETF sintético.",
            "data_referencia": "2026-09-30",
            "posicoes": [{"ticker": "XYZ", "nome": "ETF Teste", "tipo": "etf", "peso": 1.0}],
        },
        "modelo": {
            "versao_irrae": "1.1",
            "n_amostras": 2000,
            "semente": 0,
            "gerado_em": "2026-11-11T12:00:00Z",
            "cenario_faixa_carteira": "comonotonico",
        },
        "cobertura": {"peso_com_irrae": 0.6, "peso_so_prior": 0.0, "peso_nao_coberto": 0.4},
        "exposicao": {
            "setores": [
                {"id": "tecnologia", "nome": "Tecnologia", "peso": 0.9},
                {"id": "outros", "nome": "Caixa e outros ativos", "peso": 0.1},
            ],
            "temas": [
                {
                    "id": "ia",
                    "nome": "Cadeia de IA",
                    "media": 0.36,
                    "p5": 0.33,
                    "p95": 0.396,
                    "subtemas": [
                        _subtema(
                            "ia.semicondutores", "Semicondutores e hardware de IA", 0.3, 0.27, 0.336
                        ),
                        _subtema("ia.nuvem_dc", "Nuvem e data centers", 0.06, 0.048, 0.078),
                        _subtema("ia.modelos_software", "Modelos e software de IA", 0, 0, 0),
                        _subtema("ia.energia_dc", "Energia para data centers", 0, 0, 0),
                        _subtema("ia.generica", "IA sem subtema definido", 0, 0, 0),
                    ],
                }
            ],
            "fora_do_tema": 0.24,
            "nao_coberto": 0.4,
        },
        "empresas": [
            {
                "empresa_id": "US:AAA",
                "ticker": "AAA",
                "nome": "Empresa Teste A",
                "pais": "US",
                "peso_efetivo": 0.6,
                "caminho": ["XYZ"],
                "setor": "tecnologia",
                "irrae": {
                    "origem": "irrae",
                    "tema": "ia",
                    "media": 0.6,
                    "p5": 0.55,
                    "p95": 0.66,
                    "selo": "media",
                    "folhas": [
                        _subtema(
                            "ia.semicondutores", "Semicondutores e hardware de IA", 0.5, 0.45, 0.56
                        ),
                        _subtema("ia.nuvem_dc", "Nuvem e data centers", 0.1, 0.08, 0.13),
                    ],
                    "componentes": _componentes({"A_receita": 0.7, "N_narrativa": 0.3}),
                },
                "fontes": [
                    {
                        "id": "FP-03",
                        "descricao": "Relatório anual",
                        "url": "https://www.sec.gov/",
                        "data": "2026-02-01",
                    }
                ],
            },
            {
                "empresa_id": "US:BBB",
                "ticker": "BBB",
                "nome": "Empresa Teste B",
                "pais": "US",
                "peso_efetivo": 0.3,
                "caminho": ["XYZ"],
                "setor": "tecnologia",
                "irrae": {"origem": "nao_coberto"},
                "fontes": [],
            },
        ],
        "fontes_carteira": [
            {
                "id": "FP-09",
                "descricao": "Carteira do ETF",
                "url": "https://www.sec.gov/",
                "data_referencia": "2026-09-30",
            }
        ],
    }


def _recusa(dados: dict, trecho: str) -> None:
    with pytest.raises(ValidationError, match=trecho):
        Snapshot.model_validate(dados)


def test_aceita_snapshot_que_fecha():
    snapshot = Snapshot.model_validate(snapshot_valido())

    # Pesos em Decimal (backend/CLAUDE.md): o número do JSON chega exato.
    assert snapshot.exposicao.temas[0].media == Decimal("0.36")


def test_recusa_campo_que_o_contrato_nao_tem():
    # Sem campos extras, não há onde guardar CUSIP ou ISIN americano (ADR 0005).
    dados = snapshot_valido()
    dados["empresas"][0]["cusip"] = "000000000"
    _recusa(dados, "cusip")


def test_recusa_faixa_com_p5_acima_da_media():
    dados = snapshot_valido()
    dados["empresas"][0]["irrae"]["p5"] = 0.61
    _recusa(dados, "p5 <= media <= p95")


def test_recusa_carteira_cujas_posicoes_nao_somam_100():
    dados = snapshot_valido()
    dados["carteira"]["posicoes"][0]["peso"] = 0.9
    _recusa(dados, "posições da carteira")


def test_recusa_exposicao_que_nao_fecha_100():
    dados = snapshot_valido()
    dados["exposicao"]["fora_do_tema"] = 0.25
    _recusa(dados, "fecham 100%")


def test_recusa_tema_que_nao_bate_com_as_empresas():
    dados = snapshot_valido()
    tema = dados["exposicao"]["temas"][0]
    tema["media"], dados["exposicao"]["fora_do_tema"] = 0.35, 0.25
    _recusa(dados, "média do tema ia")


def test_recusa_faixa_do_tema_que_nao_e_a_soma_comonotonica():
    dados = snapshot_valido()
    dados["exposicao"]["temas"][0]["p95"] = 0.40
    _recusa(dados, "p95 do tema ia")


def test_recusa_subtema_que_nao_bate_com_as_empresas():
    dados = snapshot_valido()
    dados["exposicao"]["temas"][0]["subtemas"][1]["media"] = 0.05
    _recusa(dados, "ia.nuvem_dc")


def test_recusa_cobertura_que_nao_bate_com_as_empresas():
    dados = snapshot_valido()
    dados["cobertura"] = {"peso_com_irrae": 0.5, "peso_so_prior": 0.1, "peso_nao_coberto": 0.4}
    _recusa(dados, "cobertura")


def test_recusa_tema_fora_da_taxonomia():
    dados = snapshot_valido()
    dados["empresas"][0]["irrae"]["tema"] = "energia"
    _recusa(dados, "taxonomia")


def test_recusa_folhas_que_nao_somam_a_media_da_empresa():
    dados = snapshot_valido()
    dados["empresas"][0]["irrae"]["folhas"][1]["media"] = 0.09
    _recusa(dados, "folhas")


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "http://www.sec.gov/",
        "https://exemplo.com/",
        "https://sec.gov.exemplo.com/",
    ],
)
def test_recusa_link_de_fonte_fora_das_fontes_permitidas(url):
    # S-1 do ADR 0009: o link vira <a href> no navegador do visitante.
    dados = snapshot_valido()
    dados["empresas"][0]["fontes"][0]["url"] = url
    _recusa(dados, "link")


def test_aceita_subdominio_de_fonte_permitida():
    dados = snapshot_valido()
    dados["fontes_carteira"][0]["url"] = "https://dados.cvm.gov.br/dataset/fi-doc-cda"

    Snapshot.model_validate(dados)


@pytest.mark.parametrize("empresa_id", ["US0378331005", "AAA", "BR:CNPJ:00000000000100"])
def test_recusa_empresa_id_fora_do_adr_0005(empresa_id):
    dados = snapshot_valido()
    dados["empresas"][0]["empresa_id"] = empresa_id
    _recusa(dados, "empresa_id")


def test_recusa_empresa_repetida():
    dados = snapshot_valido()
    dados["empresas"][1]["empresa_id"] = "US:AAA"
    _recusa(dados, "repetida")


def test_recusa_numero_em_empresa_nao_coberta():
    # Empresa não coberta não tem faixa inventada (especificação, seção 5.3).
    dados = snapshot_valido()
    dados["empresas"][1]["irrae"] = {"origem": "nao_coberto", "media": 0.1}
    _recusa(dados, "não coberta")


def test_recusa_selo_que_nao_segue_a_largura_da_faixa():
    # Largura máxima 0,11 (tema): fica entre 0,10 e 0,20, então o selo é "media".
    dados = snapshot_valido()
    dados["empresas"][0]["irrae"]["selo"] = "alta"
    _recusa(dados, "selo")


def test_selo_e_preliminar_com_menos_de_dois_componentes_reais():
    dados = snapshot_valido()
    dados["empresas"][0]["irrae"]["componentes"] = _componentes(
        {"A_receita": 0.6, "prior_setorial": 0.4}
    )
    _recusa(dados, "selo")
    dados["empresas"][0]["irrae"]["selo"] = "preliminar"
    Snapshot.model_validate(dados)


def test_recusa_componente_desconhecido():
    dados = snapshot_valido()
    dados["empresas"][0]["irrae"]["componentes"][0]["id"] = "E_expectativa"
    _recusa(dados, "componentes")


def test_recusa_pesos_dos_componentes_que_nao_somam_100():
    dados = snapshot_valido()
    dados["empresas"][0]["irrae"]["componentes"] = _componentes(
        {"A_receita": 0.6, "N_narrativa": 0.3}
    )
    _recusa(dados, "peso p")


def test_recusa_setores_que_nao_fecham_100():
    dados = snapshot_valido()
    dados["exposicao"]["setores"][1]["peso"] = 0.2
    _recusa(dados, "setores")


def test_snapshot_valido_nao_e_alterado_pelas_mutacoes():
    # Guarda contra um teste acima mexer no dicionário compartilhado.
    a, b = snapshot_valido(), copy.deepcopy(snapshot_valido())
    assert a == b
