"""POST /raiox com o conjunto de exemplo sintético e o Banco Central simulado.

Carteira de referência (conta feita à mão):
- R$ 1.000 no fundo de fundos (FOF): 50% ETF de IA, 40% ETF Brasil, 10% título público;
- R$ 500 direto no Banco Exemplo.
Tema IA = 175x0,80 (chips) + 125x0,45 (nuvem) + 125x0,35 (software) + 50x0,15 (energia)
        = 140 + 56,25 + 43,75 + 7,50 = 247,50 -> 16,50% dos R$ 1.500.
"""

from datetime import date
from decimal import Decimal as D

import pytest
from fastapi.testclient import TestClient

from app.api.raiox import obter_fonte_ptax, obter_repositorio
from app.core.cambio import PtaxUsada
from app.core.identificadores import digito_verificador
from app.dados.exemplo import RepositorioExemplo
from app.dados.ptax import CambioIndisponivel
from app.main import app

FOF, BANCO, CHIPS = "ZZFOF0000016", "ZZBANCO00013", "ZZCHIPS00019"
ETF_BR, PETRO_PN, PETRO_ON = "ZZETFBR00018", "ZZPETRO00010", "ZZPETRO00028"
PTAX = PtaxUsada(date(2026, 9, 28), date(2026, 9, 25), D("5.0000"), date(2026, 9, 25))


class PtaxFalsa:
    def __init__(self, falhar: bool = False):
        self.falhar = falhar
        self.chamadas = 0

    def cotacao(self, data_pedida=None):
        self.chamadas += 1
        if self.falhar:
            raise CambioIndisponivel("simulado")
        return PTAX


@pytest.fixture
def ptax():
    return PtaxFalsa()


@pytest.fixture
def cliente(ptax):
    app.dependency_overrides[obter_repositorio] = RepositorioExemplo
    app.dependency_overrides[obter_fonte_ptax] = lambda: ptax
    yield TestClient(app)
    app.dependency_overrides.clear()


def carteira(*posicoes):
    return {"posicoes": list(posicoes)}


def pos(identificador, valor, tipo="acao", moeda="BRL", tipo_identificador="isin"):
    return {
        "tipo_identificador": tipo_identificador,
        "identificador": identificador,
        "valor": valor,
        "moeda": moeda,
        "tipo": tipo,
    }


REFERENCIA = carteira(pos(FOF, "1000.00", "fundo"), pos(BANCO, "500.00"))


def test_raio_x_da_carteira_de_referencia(cliente):
    r = cliente.post("/api/raiox", json=REFERENCIA)

    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] == "1500.00"
    tema_ia = next(t for t in corpo["por_tema"] if t["nome"] == "Cadeia de IA")
    assert (tema_ia["valor"], tema_ia["percentual"]) == ("247.50", "0.1650")
    nucleo = next(t for t in corpo["por_tema"] if t["categoria"] == "nucleo")
    sem = next(t for t in corpo["por_tema"] if t["categoria"] == "sem_classificacao")
    assert (nucleo["valor"], sem["valor"]) == ("1027.50", "80.00")
    assert corpo["versao_classificacao"] == "exemplo-v1"
    assert corpo["ptax"] is None


def test_setores_e_cobertura(cliente):
    corpo = cliente.post("/api/raiox", json=REFERENCIA).json()

    setores = {s["nome"]: s["valor"] for s in corpo["por_setor"]}
    assert setores["Financeiro"] == "660.00"  # 500 direto + 160 pelo ETF Brasil
    assert setores["Tecnologia"] == "300.00"
    assert setores[None] == "80.00"
    c = corpo["cobertura"]
    assert (c["total_acoes"], c["confirmada"], c["preliminar"], c["sem_classificacao"]) == (
        "1355.00",
        "615.00",
        "660.00",
        "80.00",
    )


def test_empresas_com_nome_e_escondidas_marcadas(cliente):
    corpo = cliente.post("/api/raiox", json=REFERENCIA).json()

    primeira = corpo["empresas"][0]
    assert primeira["empresa_id"] == "ZZ:BANCO"
    assert primeira["nome"] == "Banco Exemplo S.A."
    assert (primeira["direto"], primeira["via_fundos"], primeira["escondida"]) == (
        "500.00",
        "160.00",
        True,
    )
    assert corpo["demais_empresas"]["quantidade"] == 0


def test_categorias_fundos_e_derivativos(cliente):
    corpo = cliente.post("/api/raiox", json=REFERENCIA).json()

    assert corpo["categorias"]["titulos_publicos"] == "100.00"
    assert corpo["categorias"]["caixa"] == "35.00"
    assert corpo["categorias"]["nao_identificado"] == "5.00"
    assert {f["fundo_id"] for f in corpo["fundos"]} == {FOF, "ZZETFIA00019", ETF_BR}
    derivativo = corpo["derivativos_por_setor"][0]
    assert (derivativo["nome"], derivativo["valor"]) == ("Tecnologia", "5.00")


def test_classes_da_mesma_empresa_aparecem_numa_empresa_so_com_a_parte_de_cada_uma(cliente):
    carteira_petro = carteira(
        pos(PETRO_PN, "100.00"), pos(PETRO_ON, "50.00"), pos(ETF_BR, "1000.00", "fundo")
    )

    corpo = cliente.post("/api/raiox", json=carteira_petro).json()

    petro = [e for e in corpo["empresas"] if e["empresa_id"] == "ZZ:PETRO"]
    assert len(petro) == 1
    (e,) = petro
    assert (e["nome"], e["direto"], e["via_fundos"], e["escondida"]) == (
        "Petróleo Exemplo S.A.",
        "150.00",
        "350.00",  # 35% do ETF Brasil, na classe PN
        True,
    )
    assert e["classes"] == [
        {
            "ativo_id": PETRO_PN,
            "nome": "Petróleo Exemplo PN",
            "valor": "450.00",
            "percentual_da_empresa": "0.9000",
        },
        {
            "ativo_id": PETRO_ON,
            "nome": "Petróleo Exemplo ON",
            "valor": "50.00",
            "percentual_da_empresa": "0.1000",
        },
    ]


def test_dolar_e_convertido_pela_ptax_e_a_resposta_mostra_a_cotacao(cliente, ptax):
    corpo = cliente.post("/api/raiox", json=carteira(pos(CHIPS, "100.00", moeda="USD"))).json()

    assert corpo["total"] == "500.00"  # 100 x 5,0000
    assert corpo["ptax"] == {
        "valor": "5.0000",
        "data_cotacao": "2026-09-25",
        "data_pedida": "2026-09-28",
        "data_consulta": "2026-09-25",  # para o aviso do BCB (decisão de 14/10/2026)
    }
    assert ptax.chamadas == 1


def test_carteira_so_em_reais_nao_consulta_a_ptax(cliente, ptax):
    cliente.post("/api/raiox", json=REFERENCIA)

    assert ptax.chamadas == 0


def test_cambio_indisponivel_so_afeta_carteira_em_dolar(cliente, ptax):
    ptax.falhar = True

    em_dolar = cliente.post("/api/raiox", json=carteira(pos(CHIPS, "100.00", moeda="USD")))
    em_reais = cliente.post("/api/raiox", json=REFERENCIA)

    assert em_dolar.status_code == 503
    assert em_dolar.json()["detail"]["codigo"] == "cambio_indisponivel"
    assert em_reais.status_code == 200


def test_isin_desconhecido_entra_como_sem_classificacao(cliente):
    # ISIN válido e fictício, fora do conjunto de exemplo. Era um ISIN americano (USZQ...), que
    # agora é recusado: a ação americana entra pelo ticker (ADR 0005, seção 5).
    corpo_isin = "ZZZQ4X7K2W1"
    desconhecido = corpo_isin + digito_verificador(corpo_isin)

    corpo = cliente.post("/api/raiox", json=carteira(pos(desconhecido, "100.00"))).json()

    assert corpo["cobertura"]["sem_classificacao"] == "100.00"
    assert corpo["empresas"][0]["nome"] is None


@pytest.mark.parametrize(
    "entrada",
    [
        carteira(),  # vazia
        carteira(pos("USZQ4X7K2W18", "100.00")),  # dígito verificador errado
        carteira(pos(BANCO, "-1.00")),  # valor negativo
        carteira(pos(BANCO, "0")),  # valor zero
        carteira(pos(BANCO, "1.001")),  # mais de 2 casas
        carteira(pos(BANCO, 100.5)),  # número JSON (passaria pelo float)
        carteira(pos(BANCO, "100.00", moeda="EUR")),  # moeda fora do escopo
        carteira(pos(BANCO, "100.00", tipo="cripto")),  # tipo fora do escopo
        {"posicoes": [pos(BANCO, "100.00")], "extra": 1},  # campo desconhecido
        {"posicoes": [{**pos(BANCO, "100.00"), "nome": "x"}]},  # campo desconhecido na posição
    ],
)
def test_entrada_invalida_da_422(cliente, entrada):
    assert cliente.post("/api/raiox", json=entrada).status_code == 422


def test_limite_de_500_posicoes(cliente):
    muitas = [pos(BANCO, "1.00")] * 501

    assert cliente.post("/api/raiox", json=carteira(*muitas)).status_code == 422
    assert cliente.post("/api/raiox", json=carteira(*muitas[:500])).status_code == 200


def test_limite_de_100_fundos(cliente):
    fundos = [pos(FOF, "1.00", "fundo")] * 101

    assert cliente.post("/api/raiox", json=carteira(*fundos)).status_code == 422
    assert cliente.post("/api/raiox", json=carteira(*fundos[:100])).status_code == 200


def test_lista_de_empresas_limitada_as_200_maiores_e_o_resto_somado():
    from app.core.identificadores import digito_verificador

    isins = []
    for i in range(250):
        corpo = f"ZZT{i:08d}"
        isins.append(corpo + digito_verificador(corpo))
    posicoes = [pos(isin, f"{1000 - i}.00") for i, isin in enumerate(isins)]
    app.dependency_overrides[obter_repositorio] = RepositorioExemplo
    try:
        corpo = TestClient(app).post("/api/raiox", json=carteira(*posicoes)).json()
    finally:
        app.dependency_overrides.clear()

    assert len(corpo["empresas"]) == 200
    assert corpo["empresas"][0]["total"] == "1000.00"
    demais = corpo["demais_empresas"]
    # as 50 menores: 800 + 799 + ... + 751
    assert (demais["quantidade"], demais["valor"]) == (50, f"{sum(range(751, 801))}.00")


# --- Entrada por identificador (ADR 0005, seção 5) ---


def ticker(identificador, valor, tipo="acao", moeda="BRL"):
    return pos(identificador, valor, tipo, moeda, tipo_identificador="ticker_b3")


def test_ticker_da_b3_da_o_mesmo_raio_x_que_o_isin(cliente):
    por_isin = carteira(pos(ETF_BR, "1000.00", "fundo"), pos(BANCO, "500.00"))
    por_ticker = carteira(ticker("ZZEB11", "1000.00", "fundo"), ticker(" zzbc3 ", "500.00"))

    assert (
        cliente.post("/api/raiox", json=por_ticker).json()
        == cliente.post("/api/raiox", json=por_isin).json()
    )


def test_classes_pelo_ticker_somam_na_empresa_e_o_fracionario_e_a_mesma_acao(cliente):
    petro = carteira(ticker("ZZPT4", "100.00"), ticker("ZZPT4F", "20.00"), ticker("ZZPT3", "50.00"))

    (empresa,) = cliente.post("/api/raiox", json=petro).json()["empresas"]

    assert (empresa["empresa_id"], empresa["direto"]) == ("ZZ:PETRO", "170.00")
    assert [(c["ativo_id"], c["valor"]) for c in empresa["classes"]] == [
        (PETRO_PN, "120.00"),
        (PETRO_ON, "50.00"),
    ]


def test_ticker_desconhecido_entra_pelo_codigo_interno_sem_classificacao(cliente):
    corpo = cliente.post("/api/raiox", json=carteira(ticker("ZZZZ3", "100.00"))).json()

    assert corpo["empresas"][0]["empresa_id"] == "B3:ZZZZ3"
    assert corpo["cobertura"]["sem_classificacao"] == "100.00"


def test_tipo_da_identificacao_prevalece_sobre_o_declarado(cliente):
    # Decisão do Lucas (14/10/2026): o Banco Exemplo marcado como fundo continua ação, em vez de
    # virar "não aberto".
    corpo = cliente.post("/api/raiox", json=carteira(ticker("ZZBC3", "500.00", "fundo"))).json()

    assert (corpo["empresas"][0]["empresa_id"], corpo["empresas"][0]["direto"]) == (
        "ZZ:BANCO",
        "500.00",
    )
    assert corpo["avisos"] == []


def test_cnpj_com_mascara_e_minusculas_entra_como_fundo(cliente):
    from tests.ficticios import cnpj
    from tests.ingest.cda_sintetico import mascara

    fundo = cnpj("API-FUNDO")  # fora do conjunto de exemplo: sem composição
    entrada = carteira(pos(mascara(fundo).lower(), "100.00", "fundo", tipo_identificador="cnpj"))

    corpo = cliente.post("/api/raiox", json=entrada).json()

    assert corpo["avisos"] == [{"codigo": "fundo_sem_composicao", "fundo_id": f"CNPJ:{fundo}"}]


def test_ticker_americano_entra_pelo_us(cliente):
    entrada = carteira(pos("zzq.b", "10.00", moeda="USD", tipo_identificador="ticker_eua"))

    corpo = cliente.post("/api/raiox", json=entrada).json()

    assert corpo["empresas"][0]["empresa_id"] == "US:ZZQ.B"


def test_isin_americano_da_422_pedindo_o_ticker_sem_repetir_o_valor(cliente):
    r = cliente.post("/api/raiox", json=carteira(pos("USZQ4X7K2W17", "100.00")))

    assert r.status_code == 422
    (erro,) = r.json()["detail"]["erros"]
    assert (erro["campo"], erro["motivo"]) == (
        ["posicoes", 0, "identificador"],
        "isin_fora_da_lista",
    )
    assert "ticker" in erro["mensagem"]
    assert "USZQ" not in r.text


@pytest.mark.parametrize(
    "entrada",
    [
        carteira(ticker("ZZAA", "1.00")),  # ticker da B3 fora do formato
        carteira(pos("ZZQQQQ", "1.00", tipo_identificador="ticker_eua")),  # 6 letras
        carteira(pos("ZZAA00000000", "1.00", "fundo", tipo_identificador="cnpj")),  # dígito errado
        carteira(pos(BANCO, "1.00", tipo_identificador="cusip")),  # tipo fora do escopo
        {"posicoes": [{"isin": BANCO, "valor": "1.00", "moeda": "BRL", "tipo": "acao"}]},  # antigo
    ],
)
def test_identificador_invalido_da_422(cliente, entrada):
    assert cliente.post("/api/raiox", json=entrada).status_code == 422


# --- FIIs no raio-x (ADR 0008, etapa 4.3) ---


def test_fii_entra_na_categoria_e_nas_fatias_pelo_tipo(cliente):
    # FII marcado como ação: vale o tipo da identificação (fundo).
    entrada = carteira(ticker("ZZFL11", "300.00"), pos(BANCO, "700.00"))

    corpo = cliente.post("/api/raiox", json=entrada).json()

    assert corpo["categorias"]["fundos_imobiliarios"] == "300.00"
    assert corpo["categorias"]["nao_aberto"] == "0.00"
    assert corpo["fiis_por_tipo"] == [
        {"tipo": "tijolo", "segmento": "Logística", "valor": "300.00", "percentual": "0.3000"}
    ]
    assert corpo["avisos"] == []


def test_carteira_sem_fii_tem_a_categoria_zerada_e_nenhuma_fatia(cliente):
    corpo = cliente.post("/api/raiox", json=REFERENCIA).json()

    assert corpo["categorias"]["fundos_imobiliarios"] == "0.00"
    assert corpo["fiis_por_tipo"] == []
