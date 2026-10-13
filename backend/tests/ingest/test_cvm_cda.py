"""Leitor do CDA da CVM (ADR 0008), com arquivos sintéticos no formato da CVM."""

from datetime import date
from decimal import Decimal as D

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.composicao import ItemComposicao, TipoItem
from ingest.cvm_cda import FONTE, LayoutInesperado, ler_mes, nome_do_arquivo
from tests.ficticios import cnpj, isin
from tests.ingest.cda_sintetico import MesSintetico, peso

FUNDO, ETF, INVESTIDO = cnpj("FUNDO"), cnpj("ETF"), cnpj("INVESTIDO")
EMPRESA, BANCO = cnpj("EMPRESA"), cnpj("BANCO")
ACAO = isin("ACAO")
CPF_FICTICIO = "11111111111"  # dígitos repetidos: nunca é um CPF válido

ACOES = "Ações"
CEDIDAS = "Ações e outros TVM cedidos em empréstimo"
OBRIGACAO = "Obrigações por ações e outros TVM recebidos em empréstimo"
EXTERIOR = "Investimento no Exterior"


def mes_com_patrimonio(patrimonio: str = "1000.00") -> MesSintetico:
    return MesSintetico().patrimonio(FUNDO, patrimonio)


def itens(mes: MesSintetico, fundo: str = FUNDO) -> tuple[ItemComposicao, ...]:
    return ler_mes(mes.zip()).composicoes[f"CNPJ:{fundo}"].itens


def test_peso_e_o_valor_dividido_pelo_patrimonio_da_classe():
    mes = mes_com_patrimonio().aplicacao("fi_BLC_4", FUNDO, ACOES, "250.00", CD_ISIN=ACAO)

    lido = ler_mes(mes.zip())

    c = lido.composicoes[f"CNPJ:{FUNDO}"]
    assert c.itens == (ItemComposicao(ACAO, D("0.25"), TipoItem.ACAO),)
    assert (c.fundo_id, c.data_referencia, c.fonte) == (f"CNPJ:{FUNDO}", date(2026, 8, 31), FONTE)
    assert lido.nomes[f"CNPJ:{FUNDO}"] == "FUNDO SINTETICO"


def test_guarda_o_patrimonio_e_o_valor_de_cada_item_para_auditar():
    # ADR 0006, seção 4: o valor como a fonte informa (com o sinal da seção 4 do ADR 0008).
    mes = (
        mes_com_patrimonio()
        .aplicacao("fi_BLC_4", FUNDO, ACOES, "250.00", CD_ISIN=ACAO)
        .aplicacao("fi_BLC_8", FUNDO, "Valores a pagar", "50.00", TP_ATIVO="Outros")
    )

    lido = ler_mes(mes.zip())

    fundo = f"CNPJ:{FUNDO}"
    assert lido.patrimonio[fundo] == D("1000.00")
    assert lido.valores[fundo] == (D("250.00"), D("-50.00"))
    # Um valor para cada item, na mesma ordem: valor ÷ patrimônio = peso.
    for item, valor in zip(lido.composicoes[fundo].itens, lido.valores[fundo], strict=True):
        assert valor / lido.patrimonio[fundo] == item.peso


@pytest.mark.parametrize(
    ("arquivo", "tp_aplic", "tp_ativo", "tipo", "sinal"),
    [
        ("fi_BLC_1", "Títulos Públicos", "Título público federal", TipoItem.TITULO_PUBLICO, 1),
        ("fi_BLC_1", "Operações Compromissadas", "Título público federal", TipoItem.CAIXA, 1),
        ("fi_BLC_3", "DIFERENCIAL DE SWAP A RECEBER", "SWAP", TipoItem.DERIVATIVO, 1),
        ("fi_BLC_3", "DIFERENCIAL DE SWAP A PAGAR", "SWAP", TipoItem.DERIVATIVO, -1),
        ("fi_BLC_4", "Debêntures", "Debênture simples", TipoItem.CREDITO, 1),
        ("fi_BLC_4", "Opções - Posições titulares", "Opção de compra", TipoItem.DERIVATIVO, 1),
        ("fi_BLC_4", "Opções - Posições lançadas", "Opção de venda", TipoItem.DERIVATIVO, -1),
        (
            "fi_BLC_4",
            "Mercado Futuro - Posições compradas",
            "Contrato Futuro",
            TipoItem.DERIVATIVO,
            1,
        ),
        ("fi_BLC_8", "Valores a receber", "Outros", TipoItem.CAIXA, 1),
        ("fi_BLC_8", "Valores a pagar", "Outros", TipoItem.CAIXA, -1),
        ("fi_BLC_8", "Disponibilidades", "Outros", TipoItem.CAIXA, 1),
        ("fi_BLC_8", "Outras operações passivas e exigibilidades", "Outros", TipoItem.CAIXA, -1),
        ("fi_BLC_8", "Obrigações por compra a termo a pagar", "Outros", TipoItem.DERIVATIVO, -1),
        ("fi_BLC_8", "Obrigações por venda a termo a entregar", "Outros", TipoItem.DERIVATIVO, -1),
        ("fi_BLC_8", "Vendas a termo a receber", "Outros", TipoItem.DERIVATIVO, 1),
        (
            "fi_BLC_8",
            "Outras aplicações",
            "Outros instrumentos derivativos",
            TipoItem.DERIVATIVO,
            1,
        ),
        ("fi_BLC_8", "Outras aplicações", "Outros", TipoItem.OUTRO, 1),
        (
            "fi_BLC_8",
            "Outros valores mobiliários registrados na CVM objeto de oferta pública",
            "Certificado de recebíveis imobiliários",
            TipoItem.CREDITO,
            1,
        ),
        (
            "fi_BLC_8",
            "Outros valores mobiliários ofertados privadamente",
            "Bônus de subscrição",
            TipoItem.OUTRO,
            1,
        ),
        ("fi_BLC_6", "Títulos ligados ao agronegócio", "CRA", TipoItem.CREDITO, 1),
        ("fi_BLC_6", "Títulos de Crédito Privado", "CCB", TipoItem.CREDITO, 1),
        ("fi_BLC_7", EXTERIOR, "Título da Dívida Externa", TipoItem.TITULO_PUBLICO, 1),
        ("fi_BLC_7", EXTERIOR, "Bonds e Treasury", TipoItem.OUTRO, 1),
        ("fi_BLC_7", EXTERIOR, "Opção de compra", TipoItem.DERIVATIVO, 1),
        ("fi_BLC_7", EXTERIOR, "Outros", TipoItem.OUTRO, 1),
    ],
)
def test_cada_tipo_de_aplicacao_vira_um_tipo_do_motor_com_o_sinal_certo(
    arquivo, tp_aplic, tp_ativo, tipo, sinal
):
    mes = mes_com_patrimonio().aplicacao(arquivo, FUNDO, tp_aplic, "100.00", TP_ATIVO=tp_ativo)

    (item,) = itens(mes)

    assert (item.tipo, item.peso) == (tipo, sinal * D("0.1"))


def test_obrigacao_por_acao_recebida_em_emprestimo_vira_posicao_vendida():
    mes = mes_com_patrimonio().aplicacao(
        "fi_BLC_4", FUNDO, OBRIGACAO, "100.00", TP_ATIVO="Ação ordinária", CD_ISIN=ACAO
    )

    assert itens(mes) == (ItemComposicao(ACAO, D("-0.1"), TipoItem.ACAO),)


def test_acao_recebida_em_emprestimo_que_o_fundo_ainda_tem_se_anula():
    mes = (
        mes_com_patrimonio()
        .aplicacao("fi_BLC_4", FUNDO, ACOES, "100.00", CD_ISIN=ACAO)
        .aplicacao("fi_BLC_4", FUNDO, OBRIGACAO, "100.00", CD_ISIN=ACAO)
    )

    assert itens(mes) == ()


def test_acoes_cedidas_em_emprestimo_somam_com_as_do_bloco_de_acoes():
    mes = (
        mes_com_patrimonio()
        .aplicacao("fi_BLC_4", FUNDO, ACOES, "100.00", CD_ISIN=ACAO)
        .aplicacao("fi_BLC_4", FUNDO, CEDIDAS, "50.00", CD_ISIN=ACAO)
    )

    assert itens(mes) == (ItemComposicao(ACAO, D("0.15"), TipoItem.ACAO),)


@pytest.mark.parametrize("tp_ativo", ["Fundos de Índice", "FI Imobiliário", "BDR de ETF"])
def test_cota_de_fundo_dentro_de_linha_de_acao_vira_fundo_sem_identificador(tp_ativo):
    mes = mes_com_patrimonio().aplicacao("fi_BLC_8", FUNDO, CEDIDAS, "100.00", TP_ATIVO=tp_ativo)

    assert itens(mes) == (ItemComposicao(None, D("0.1"), TipoItem.FUNDO),)


def test_cota_de_outro_fundo_aponta_para_o_cnpj_da_classe_investida():
    mes = mes_com_patrimonio().aplicacao(
        "fi_BLC_2", FUNDO, "Cotas de Fundos", "300.00", CNPJ_FUNDO_CLASSE_COTA=INVESTIDO
    )

    assert itens(mes) == (ItemComposicao(f"CNPJ:{INVESTIDO}", D("0.3"), TipoItem.FUNDO),)


def test_fundo_offshore_entra_como_fundo_sem_identificador():
    mes = mes_com_patrimonio().aplicacao(
        "fi_BLC_7", FUNDO, EXTERIOR, "100.00", TP_ATIVO="Fundos Offshore", CD_BV_MERC="99"
    )

    assert itens(mes) == (ItemComposicao(None, D("0.1"), TipoItem.FUNDO),)


def test_credito_de_banco_tem_o_banco_como_emissor():
    mes = mes_com_patrimonio().aplicacao(
        "fi_BLC_5",
        FUNDO,
        "Depósitos a prazo e outros títulos de IF",
        "100.00",
        TP_ATIVO="CDB/ RDB",
        CNPJ_EMISSOR=BANCO,
    )

    assert itens(mes) == (
        ItemComposicao(None, D("0.1"), TipoItem.CREDITO, emissor=f"BR:CNPJ:{BANCO}"),
    )


def test_cpf_de_emissor_pessoa_fisica_nunca_sai_do_leitor():
    mes = mes_com_patrimonio().aplicacao(
        "fi_BLC_6",
        FUNDO,
        "Títulos de Crédito Privado",
        "100.00",
        TP_ATIVO="CCB",
        PF_PJ_EMISSOR="PF",
        CPF_CNPJ_EMISSOR=CPF_FICTICIO,
    )

    lido = ler_mes(mes.zip())

    assert lido.composicoes[f"CNPJ:{FUNDO}"].itens == (
        ItemComposicao(None, D("0.1"), TipoItem.CREDITO),
    )
    assert CPF_FICTICIO not in repr(lido)


def test_emissor_pessoa_juridica_liga_o_credito_a_empresa():
    mes = mes_com_patrimonio().aplicacao(
        "fi_BLC_6",
        FUNDO,
        "Debêntures",
        "100.00",
        TP_ATIVO="Debênture simples",
        PF_PJ_EMISSOR="PJ",
        CPF_CNPJ_EMISSOR=EMPRESA,
    )

    assert itens(mes) == (
        ItemComposicao(None, D("0.1"), TipoItem.CREDITO, emissor=f"BR:CNPJ:{EMPRESA}"),
    )


def etf_com(**campos: str) -> MesSintetico:
    """Mês com uma ação dentro de um ETF (arquivo `fie`, com o patrimônio na própria linha)."""
    return MesSintetico().aplicacao(
        "fie", ETF, ACOES, "400.00", VL_PATRIM_LIQ="1000.00", TP_ATIVO="Ação ordinária", **campos
    )


def test_ticker_do_etf_vira_isin_pelo_bloco_de_acoes():
    mes = (
        etf_com(CD_ATIVO="ZZAA3")
        .patrimonio(FUNDO, "1000.00")
        .aplicacao("fi_BLC_4", FUNDO, ACOES, "1.00", CD_ATIVO="ZZAA3", CD_ISIN=ACAO)
    )

    lido = ler_mes(mes.zip())

    assert lido.composicoes[f"CNPJ:{ETF}"].itens == (ItemComposicao(ACAO, D("0.4"), TipoItem.ACAO),)
    assert lido.isin_do_ticker == {"ZZAA3": ACAO}


def test_acao_do_etf_sem_par_no_bloco_de_acoes_liga_a_empresa_pelo_cnpj_do_emissor():
    mes = etf_com(CD_ATIVO="ZZAA3", PF_PJ_EMISSOR="PJ", CPF_CNPJ_EMISSOR=EMPRESA)

    assert itens(mes, ETF) == (
        ItemComposicao(None, D("0.4"), TipoItem.ACAO, empresa_id=f"BR:CNPJ:{EMPRESA}"),
    )


def test_ticker_com_dois_isins_diferentes_nao_e_usado():
    mes = (
        etf_com(CD_ATIVO="ZZAA3")
        .patrimonio(FUNDO, "1000.00")
        .aplicacao("fi_BLC_4", FUNDO, ACOES, "1.00", CD_ATIVO="ZZAA3", CD_ISIN=ACAO)
        .aplicacao("fi_BLC_4", FUNDO, ACOES, "1.00", CD_ATIVO="ZZAA3", CD_ISIN=isin("OUTRA"))
    )

    lido = ler_mes(mes.zip())

    assert lido.composicoes[f"CNPJ:{ETF}"].itens == ()
    assert "ZZAA3" not in lido.isin_do_ticker


def test_acao_sem_identificacao_fica_fora_e_entra_no_nao_identificado():
    lido = ler_mes(etf_com().zip())

    assert lido.composicoes[f"CNPJ:{ETF}"].itens == ()
    assert lido.descartes["acao_sem_identificacao"] == 1
    assert lido.soma_das_linhas[f"CNPJ:{ETF}"] == D("0.4")


@pytest.mark.parametrize("codigo", ["ZZQ", "ZZQ US", "ZZQ UN", "ZZQ.B", " zzq us "])
def test_acao_em_bolsa_americana_vira_us_mais_ticker(codigo):
    mes = mes_com_patrimonio().aplicacao(
        "fi_BLC_7",
        FUNDO,
        EXTERIOR,
        "100.00",
        TP_ATIVO="Ação ordinária",
        CD_BV_MERC="A11",
        CD_ATIVO_BV_MERC=codigo,
    )

    (item,) = itens(mes)

    assert item.ativo_id == "US:" + codigo.strip().upper().split()[0]
    assert (item.tipo, item.peso) == (TipoItem.ACAO, D("0.1"))


@pytest.mark.parametrize(
    ("bolsa", "codigo"),
    [
        ("A12", "99999ZZZ9"),  # formato de CUSIP
        ("A12", "0000001"),  # formato de SEDOL
        ("A11", isin("EXTERIOR")),  # formato de ISIN
        ("A1", "123"),  # número interno
        ("E14", "ZZQ LN"),  # ticker de bolsa fora dos EUA
    ],
)
def test_codigo_do_exterior_que_nao_e_ticker_americano_e_descartado(bolsa, codigo):
    mes = mes_com_patrimonio().aplicacao(
        "fi_BLC_7",
        FUNDO,
        EXTERIOR,
        "100.00",
        TP_ATIVO="Depository Receipt no Exterior(DR)",
        CD_BV_MERC=bolsa,
        CD_ATIVO_BV_MERC=codigo,
    )

    lido = ler_mes(mes.zip())

    assert lido.composicoes[f"CNPJ:{FUNDO}"].itens == ()
    assert codigo not in repr(lido)


def test_parte_confidencial_entra_pelo_valor_liquido_e_fora_dos_itens():
    mes = (
        mes_com_patrimonio()
        .aplicacao("fi_CONFID", FUNDO, ACOES, "300")
        .aplicacao("fi_CONFID", FUNDO, "Valores a pagar", "100")
    )

    lido = ler_mes(mes.zip())

    assert lido.confidencial == {f"CNPJ:{FUNDO}": D("0.2")}
    assert lido.composicoes[f"CNPJ:{FUNDO}"].itens == ()


@pytest.mark.parametrize("patrimonio", ["0.00", "-10.00"])
def test_fundo_com_patrimonio_zero_ou_negativo_fica_sem_composicao_utilizavel(patrimonio):
    mes = mes_com_patrimonio(patrimonio).aplicacao("fi_BLC_4", FUNDO, ACOES, "100.00", CD_ISIN=ACAO)

    lido = ler_mes(mes.zip())

    assert f"CNPJ:{FUNDO}" not in lido.composicoes
    assert lido.sem_composicao_utilizavel == {f"CNPJ:{FUNDO}"}
    assert lido.descartes["fundo_com_patrimonio_zero_ou_negativo"] == 1


def test_fundo_com_aplicacoes_e_sem_patrimonio_fica_sem_composicao_utilizavel():
    mes = MesSintetico().aplicacao("fi_BLC_4", FUNDO, ACOES, "100.00", CD_ISIN=ACAO)

    lido = ler_mes(mes.zip())

    assert lido.sem_composicao_utilizavel == {f"CNPJ:{FUNDO}"}
    assert lido.descartes["fundo_sem_patrimonio"] == 1


def test_data_invalida_no_patrimonio_e_descartada_e_contada():
    mes = mes_com_patrimonio().aplicacao("fi_BLC_4", FUNDO, ACOES, "100.00", CD_ISIN=ACAO)
    mes.linhas["fi_PL"][0]["DT_COMPTC"] = "31/08/2026"

    lido = ler_mes(mes.zip())

    assert lido.sem_composicao_utilizavel == {f"CNPJ:{FUNDO}"}
    assert lido.descartes["data_invalida"] == 1


def test_soma_das_linhas_conta_passivos_confidencial_e_o_que_nao_foi_identificado():
    mes = (
        mes_com_patrimonio()
        .aplicacao("fi_BLC_4", FUNDO, ACOES, "500.00", CD_ISIN=ACAO)
        .aplicacao("fi_BLC_8", FUNDO, "Valores a pagar", "100.00", TP_ATIVO="Outros")
        .aplicacao("fi_BLC_4", FUNDO, ACOES, "200.00")  # sem ISIN: não identificada
        .aplicacao("fi_CONFID", FUNDO, ACOES, "400")
    )

    assert ler_mes(mes.zip()).soma_das_linhas == {f"CNPJ:{FUNDO}": D("1")}


@pytest.mark.parametrize("valor", ["NaN", "Infinity", "1,5", "1e3", ""])
def test_valor_fora_do_formato_e_descartado_e_contado(valor):
    mes = mes_com_patrimonio().aplicacao("fi_BLC_4", FUNDO, ACOES, valor, CD_ISIN=ACAO)

    lido = ler_mes(mes.zip())

    assert lido.composicoes[f"CNPJ:{FUNDO}"].itens == ()
    assert lido.descartes["valor_invalido"] == 1


def test_arquivo_faltando_para_a_leitura():
    with pytest.raises(LayoutInesperado, match="cda_fi_BLC_3_202608.csv"):
        ler_mes(mes_com_patrimonio().zip(sem=("fi_BLC_3",)))


def test_arquivo_a_mais_para_a_leitura():
    with pytest.raises(LayoutInesperado, match="cda_fi_BLC_9_202608.csv"):
        ler_mes(mes_com_patrimonio().zip(extras=("cda_fi_BLC_9_202608.csv",)))


def test_layout_antigo_dos_etfs_para_a_leitura():
    # Antes de 15/11/2025 os ETFs vinham em cda_fiim (matriz de dados, fonte 1).
    mes = mes_com_patrimonio()
    with pytest.raises(LayoutInesperado, match="cda_fiim_202608.csv"):
        ler_mes(mes.zip(sem=("fie",), extras=("cda_fiim_202608.csv",)))


def test_coluna_diferente_para_a_leitura():
    from ingest.cvm_cda import COLUNAS

    sem_isin = tuple(c for c in COLUNAS["fi_BLC_4"] if c != "CD_ISIN")
    with pytest.raises(LayoutInesperado, match="CD_ISIN"):
        ler_mes(mes_com_patrimonio().zip(colunas={"fi_BLC_4": sem_isin}))


def test_tipo_de_aplicacao_desconhecido_para_a_leitura():
    mes = mes_com_patrimonio().aplicacao("fi_BLC_8", FUNDO, "Aplicação nova", "1.00")

    with pytest.raises(LayoutInesperado, match="Aplicação nova"):
        ler_mes(mes.zip())


def test_nome_do_arquivo_segue_o_padrao_da_cvm():
    assert nome_do_arquivo("fi_BLC_4", "202608") == "cda_fi_BLC_4_202608.csv"
    assert nome_do_arquivo("fie_CONFID", "202608") == "cda_fie_CONFID_202608.csv"


valores = st.decimals(min_value=D("0.01"), max_value=D("1000000"), places=2)


@settings(deadline=None, max_examples=30)
@given(
    st.lists(
        st.tuples(st.sampled_from([ACAO, isin("B"), isin("C")]), valores), min_size=1, max_size=8
    )
)
def test_peso_das_acoes_se_conserva(linhas):
    mes = mes_com_patrimonio("1000000.00")
    for ativo, valor in linhas:
        mes.aplicacao("fi_BLC_4", FUNDO, ACOES, str(valor), CD_ISIN=ativo)

    lido = ler_mes(mes.zip())

    total = sum((item.peso for item in lido.composicoes[f"CNPJ:{FUNDO}"].itens), D(0))
    assert total == sum((peso(str(v), "1000000.00") for _, v in linhas), D(0))
