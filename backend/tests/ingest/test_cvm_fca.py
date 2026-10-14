"""Leitor do FCA da CVM (matriz de dados, fonte 4; ADR 0008, etapa 4), com pacotes sintéticos."""

import io
import zipfile

import pytest

from ingest.arquivos_cvm import LayoutInesperado
from ingest.cvm_fca import COLUNAS, ler_fca
from tests.ficticios import cnpj
from tests.ingest.fca_sintetico import AnoSintetico

EMPRESA_A, EMPRESA_B = cnpj("FCA-A"), cnpj("FCA-B")


def test_vale_a_versao_mais_recente_de_cada_companhia_juntando_os_anos():
    antigo = AnoSintetico("2025").companhia(EMPRESA_A, "ZZAA3", setor="Setor Antigo")
    novo = (
        AnoSintetico("2026")
        .companhia(EMPRESA_A, "ZZAA3", versao="1", setor="Setor Velho Deste Ano")
        .companhia(EMPRESA_A, "ZZAA3", "ZZAA4", versao="2", setor="Setor Novo", nome="NOVO S.A.")
    )

    lido = ler_fca([antigo.zip(), novo.zip()])

    a = lido.companhias[EMPRESA_A]
    assert (a.cnpj, a.nome, a.setor) == (EMPRESA_A, "NOVO S.A.", "Setor Novo")
    assert lido.cnpj_do_ticker == {"ZZAA3": EMPRESA_A, "ZZAA4": EMPRESA_A}


def test_raiz_do_ticker_liga_a_companhia():
    lido = ler_fca([AnoSintetico().companhia(EMPRESA_A, "ZZAA3", "ZZAA11").zip()])

    assert lido.cnpj_da_raiz == {"ZZAA": EMPRESA_A}


@pytest.mark.parametrize("codigo", ["000000", "4030", "ADR", "", "ZZAA", "ZZAA123"])
def test_codigo_fora_do_formato_da_b3_nao_vira_ticker(codigo):
    # Casos reais de códigos preenchidos errado pelas companhias (ADR 0008, etapa 4).
    lido = ler_fca([AnoSintetico().companhia(EMPRESA_A, codigo).zip()])

    assert lido.cnpj_do_ticker == {}
    assert lido.cnpj_da_raiz == {}
    assert EMPRESA_A in lido.companhias  # a companhia continua, com o setor


def test_raiz_com_numero_e_aceita():
    lido = ler_fca([AnoSintetico().companhia(EMPRESA_A, "Z3ZA3").zip()])

    assert lido.cnpj_da_raiz == {"Z3ZA": EMPRESA_A}


@pytest.mark.parametrize(
    "campos",
    [
        {"Valor_Mobiliario": "Debêntures"},
        {"Valor_Mobiliario": "Bônus de Subscrição"},
        {"Data_Fim_Negociacao": "2026-03-31"},
    ],
)
def test_so_acoes_e_units_negociadas_viram_ticker(campos):
    lido = ler_fca([AnoSintetico().companhia(EMPRESA_A, "ZZAA3", **campos).zip()])

    assert lido.cnpj_do_ticker == {}


def test_units_e_preferenciais_viram_ticker():
    ano = (
        AnoSintetico()
        .companhia(EMPRESA_A, "ZZAA11", Valor_Mobiliario="Units")
        .companhia(EMPRESA_B, "ZZBB4", Valor_Mobiliario="Ações Preferenciais")
    )

    assert ler_fca([ano.zip()]).cnpj_do_ticker == {"ZZAA11": EMPRESA_A, "ZZBB4": EMPRESA_B}


def test_raiz_ou_ticker_de_duas_companhias_nao_e_usado():
    ano = AnoSintetico().companhia(EMPRESA_A, "ZZAA3").companhia(EMPRESA_B, "ZZAA4", "ZZAA3")

    lido = ler_fca([ano.zip()])

    assert lido.cnpj_da_raiz == {}
    assert lido.cnpj_do_ticker == {"ZZAA4": EMPRESA_B}
    assert lido.descartes["raiz_com_duas_companhias"] == 1
    assert lido.descartes["ticker_com_duas_companhias"] == 1


def test_nunca_abre_os_arquivos_com_dados_pessoais(monkeypatch):
    pacote = AnoSintetico().companhia(EMPRESA_A, "ZZAA3").zip()  # antes de espiar
    abertos = []
    abrir = zipfile.ZipFile.open

    def espiar(self, nome, *args, **kwargs):
        abertos.append(nome if isinstance(nome, str) else nome.filename)
        return abrir(self, nome, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "open", espiar)

    ler_fca([pacote])

    assert sorted(abertos) == [
        "fca_cia_aberta_geral_2026.csv",
        "fca_cia_aberta_valor_mobiliario_2026.csv",
    ]


def test_coluna_diferente_para_a_leitura():
    sem_setor = tuple(c for c in COLUNAS["geral"] if c != "Setor_Atividade")

    with pytest.raises(LayoutInesperado, match="Setor_Atividade"):
        ler_fca([AnoSintetico().companhia(EMPRESA_A).zip(colunas={"geral": sem_setor})])


def test_pacote_sem_a_tabela_geral_para_a_leitura():
    saida = AnoSintetico().companhia(EMPRESA_A).zip()
    with zipfile.ZipFile(saida) as z:
        vm = z.read("fca_cia_aberta_valor_mobiliario_2026.csv")
    incompleto = io.BytesIO()
    with zipfile.ZipFile(incompleto, "w") as z:
        z.writestr("fca_cia_aberta_valor_mobiliario_2026.csv", vm)
    incompleto.seek(0)

    with pytest.raises(LayoutInesperado, match="fca_cia_aberta_geral_AAAA.csv"):
        ler_fca([incompleto])
