"""Montagem da identificação e do setor oficial (ADR 0008, etapa 4), sem banco, a partir de arquivos
sintéticos nos formatos da CVM."""

from pathlib import Path

import pytest

from cargas.identificacao import Ativo, Curadoria, Empresa, Setor, ler_curadoria, montar
from ingest.cvm_cda import MesCDA, ler_mes
from ingest.cvm_fca import CadastroFCA, ler_fca
from ingest.cvm_fii import InformesFII, ler_informes_fii
from tests.ficticios import cnpj, isin_da_raiz
from tests.ingest.cda_sintetico import MesSintetico
from tests.ingest.fca_sintetico import AnoSintetico
from tests.ingest.fii_sintetico import AnoFII

EMPRESA, OUTRA = cnpj("ID-EMPRESA"), cnpj("ID-OUTRA")
ETF, FII, FUNDO = cnpj("ID-ETF"), cnpj("ID-FII"), cnpj("ID-FUNDO")
ON, PN = isin_da_raiz("ZZAA", "ACNOR"), isin_da_raiz("ZZAA", "ACNPR")
CEDIDAS = "Ações e outros TVM cedidos em empréstimo"
SEM_CURADORIA = Curadoria(emissores={}, fundos_listados={})


def fca(*companhias: tuple[str, ...]) -> CadastroFCA:
    """FCA com uma companhia por tupla (CNPJ, tickers...)."""
    ano = AnoSintetico()
    for cnpj_da_companhia, *tickers in companhias:
        ano.companhia(cnpj_da_companhia, *tickers)
    return ler_fca([ano.zip()])


def cda(*pares: tuple[str, str], listados: tuple[tuple[str, str], ...] = ()) -> MesCDA:
    """Mês do CDA com um fundo que tem uma ação por par (ticker, ISIN) e cotas emprestadas de cada
    fundo listado (ticker, CNPJ)."""
    mes = MesSintetico().patrimonio(FUNDO, "1000.00")
    for ticker, isin in pares:
        mes.aplicacao("fi_BLC_4", FUNDO, "Ações", "1.00", CD_ATIVO=ticker, CD_ISIN=isin)
    for ticker, cnpj_do_fundo in listados:
        mes.aplicacao(
            "fi_BLC_8",
            FUNDO,
            CEDIDAS,
            "1.00",
            TP_ATIVO="Fundos de Índice",
            DS_ATIVO=ticker,
            PF_PJ_EMISSOR="PJ",
            CPF_CNPJ_EMISSOR=cnpj_do_fundo,
        )
    return ler_mes(mes.zip())


def fiis(*fundos: dict) -> InformesFII:
    ano = AnoFII()
    for campos in fundos:
        ano.fundo(**campos)
    return ler_informes_fii([ano.zip()])


def montar_com(
    cadastro: CadastroFCA,
    meses: list[MesCDA] | None = None,
    informes: InformesFII | None = None,
    curadoria: Curadoria = SEM_CURADORIA,
):
    return montar(cadastro, meses or [cda()], informes or fiis(), curadoria)


def ativos(identificacao) -> dict[str, Ativo]:
    return {a.ativo_id: a for a in identificacao.ativos}


def test_acao_do_cda_fica_pelo_isin_e_a_raiz_liga_a_companhia():
    ident = montar_com(fca((EMPRESA, "ZZAA3")), [cda(("ZZAA4", PN))])

    assert ativos(ident)[PN] == Ativo(
        ativo_id=PN, tipo="acao", empresa_id=f"BR:CNPJ:{EMPRESA}", ticker_b3="ZZAA4", isin=PN,
        nome="ZZAA4",
    )  # fmt: skip


def test_ticker_que_so_o_fca_conhece_ganha_o_codigo_interno_da_b3():
    ident = montar_com(fca((EMPRESA, "ZZAA3")), [cda(("ZZAA4", PN))])

    assert ativos(ident)["B3:ZZAA3"] == Ativo(
        ativo_id="B3:ZZAA3", tipo="acao", empresa_id=f"BR:CNPJ:{EMPRESA}", ticker_b3="ZZAA3",
        isin=None, nome="ZZAA3",
    )  # fmt: skip


def test_ticker_que_o_cda_liga_a_um_isin_nao_ganha_codigo_interno():
    ident = montar_com(fca((EMPRESA, "ZZAA3")), [cda(("ZZAA3", ON))])

    assert set(ativos(ident)) == {ON}
    assert ativos(ident)[ON].ticker_b3 == "ZZAA3"


def test_isin_que_so_aparece_nas_composicoes_tambem_e_ligado_pela_raiz():
    ident = montar_com(fca((EMPRESA, "ZZAA3")), [cda(("", ON))])

    assert ativos(ident)[ON].empresa_id == f"BR:CNPJ:{EMPRESA}"
    assert ativos(ident)[ON].ticker_b3 is None


def test_acao_sem_companhia_conhecida_fica_de_fora():
    # Ex.: um BDR, de empresa de fora, que não entrega FCA.
    bdr = isin_da_raiz("ZZBB", "BDR00")

    ident = montar_com(fca((EMPRESA, "ZZAA3")), [cda(("ZZBB34", bdr))])

    assert bdr not in ativos(ident)
    assert ident.descartes["acao_sem_companhia"] == 1


def test_curadoria_liga_a_raiz_que_o_fca_traz_com_codigo_errado():
    curadoria = Curadoria(emissores={"ZZAA": (EMPRESA, "COMPANHIA")}, fundos_listados={})
    unit = isin_da_raiz("ZZAA", "UNT00")

    ident = montar_com(fca((EMPRESA, "000000")), [cda(("ZZAA11", unit))], curadoria=curadoria)

    assert ativos(ident)[unit].empresa_id == f"BR:CNPJ:{EMPRESA}"


def test_curadoria_cria_a_companhia_que_nao_esta_no_fca():
    curadoria = Curadoria(emissores={"ZZAA": (OUTRA, "OUTRA S.A.")}, fundos_listados={})

    ident = montar_com(fca((EMPRESA, "ZZBB3")), [cda(("ZZAA3", ON))], curadoria=curadoria)

    assert Empresa(f"BR:CNPJ:{OUTRA}", "OUTRA S.A.", OUTRA) in ident.empresas
    assert ativos(ident)[ON].empresa_id == f"BR:CNPJ:{OUTRA}"


def test_no_par_ticker_isin_vale_o_mes_mais_recente():
    novo, velho = cda(("ZZAA3", ON)), cda(("ZZAA3", PN))

    ident = montar_com(fca((EMPRESA, "ZZAA3")), [novo, velho])

    assert ativos(ident)[ON].ticker_b3 == "ZZAA3"
    assert ativos(ident)[PN].ticker_b3 is None  # continua ligado à companhia, sem o ticker


def test_etf_e_fii_listados_entram_com_ticker_e_o_fii_com_o_tipo():
    isin_do_fii = isin_da_raiz("ZZFI", "CTF00")
    informes = fiis(dict(cnpj=FII, isin=isin_do_fii, nome="FII", Direitos_Bens_Imoveis="1"))
    meses = [cda(listados=(("ZZTF11", ETF), ("ZZFI11", FII)))]

    ident = montar_com(fca(), meses, informes)

    assert ativos(ident)[f"CNPJ:{ETF}"] == Ativo(
        ativo_id=f"CNPJ:{ETF}", tipo="fundo", empresa_id=None, ticker_b3="ZZTF11", isin=None,
        nome=None,
    )  # fmt: skip
    assert ativos(ident)[f"CNPJ:{FII}"] == Ativo(
        ativo_id=f"CNPJ:{FII}", tipo="fundo", empresa_id=None, ticker_b3="ZZFI11",
        isin=isin_do_fii, nome="FII", fii_tipo="tijolo", fii_segmento="Logística",
    )  # fmt: skip


def test_fii_sem_ticker_conhecido_entra_pelo_isin():
    isin_do_fii = isin_da_raiz("ZZFI", "CTF00")

    ident = montar_com(fca(), informes=fiis(dict(cnpj=FII, isin=isin_do_fii, CRI_CRA="1")))

    fii = ativos(ident)[f"CNPJ:{FII}"]
    assert (fii.ticker_b3, fii.isin, fii.fii_tipo) == (None, isin_do_fii, "papel")


def test_curadoria_de_fundo_listado_vale_mais_que_o_cda():
    curadoria = Curadoria(emissores={}, fundos_listados={"ZZTF11": ETF})

    ident = montar_com(fca(), [cda(listados=(("ZZTF11", FII),))], curadoria=curadoria)

    assert ativos(ident)[f"CNPJ:{ETF}"].ticker_b3 == "ZZTF11"
    assert f"CNPJ:{FII}" not in ativos(ident)


def test_setor_oficial_de_cada_companhia_do_fca():
    ident = montar_com(fca((EMPRESA, "ZZAA3")))

    assert ident.setores == [Setor(f"BR:CNPJ:{EMPRESA}", "Setor Sintético")]
    assert ident.empresas == [Empresa(f"BR:CNPJ:{EMPRESA}", "COMPANHIA SINTETICA S.A.", EMPRESA)]


# --- Arquivos de curadoria ---

CURADORIA = Path(__file__).resolve().parents[2] / "cargas" / "curadoria"


def test_curadoria_do_repositorio_e_valida():
    curadoria = ler_curadoria(CURADORIA)

    assert set(curadoria.emissores) == {"BPAC", "CSNA", "CMIN", "MBRF", "EGGY"}


@pytest.mark.parametrize(
    ("linha", "erro"),
    [
        ("ZZAA;12345678000100;NOME;motivo", "CNPJ"),  # dígito verificador errado
        ("3ZAA;30306294000145;NOME;motivo", "raiz"),  # raiz começando por número
    ],
)
def test_curadoria_com_linha_errada_para_a_carga(tmp_path, linha, erro):
    (tmp_path / "emissores_b3.csv").write_text(
        f"raiz;cnpj;nome;motivo\n{linha}\n", encoding="utf-8"
    )
    (tmp_path / "fundos_listados.csv").write_text("ticker;cnpj;nome;fonte\n", encoding="utf-8")

    with pytest.raises(ValueError, match=f"emissores_b3.csv, linha 2: {erro}"):
        ler_curadoria(tmp_path)
