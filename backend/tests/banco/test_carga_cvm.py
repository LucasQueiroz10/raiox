"""Carga das composições da CVM no banco (ADR 0008, etapa 3), com zips sintéticos e rx_ingestao.

Cada teste usa um banco novo: o resultado depende do que já foi publicado para o mesmo mês.
"""

from dataclasses import replace
from datetime import date
from decimal import Decimal as D

import pytest

from app.core.composicao import ItemComposicao, TipoItem
from cargas import cvm
from cargas.cvm import TIPO, carregar_mes
from cargas.rotina import ErroDeValidacao
from ingest.cvm_cda import FONTE, LayoutInesperado, MesCDA, ler_mes
from tests.ficticios import cnpj, isin
from tests.ingest.cda_sintetico import MesSintetico

FUNDO_A, FUNDO_B = cnpj("CARGA-A"), cnpj("CARGA-B")
ACAO = isin("CARGA-ACAO")
CPF_DE_TESTE = "00000000191"  # o mesmo número de teste de tests/cargas/test_validacao.py


def mes_com(*fundos: tuple[str, str], nome: str = "FUNDO SINTETICO") -> MesSintetico:
    """Mês com um fundo por par (CNPJ, valor da ação), cada um com patrimônio de 1000."""
    mes = MesSintetico()
    for fundo, valor in fundos:
        mes.patrimonio(fundo, "1000.00", nome=nome)
        mes.aplicacao("fi_BLC_4", fundo, "Ações", valor, CD_ISIN=ACAO)
    return mes


def carregar(conexao, mes: MesSintetico, **zip_kw):
    return carregar_mes(conexao, "202608", lambda: mes.zip(**zip_kw))


def cargas(conexao) -> list[tuple]:
    return conexao.execute(
        "SELECT status, motivo_erro FROM ref.carga WHERE tipo = %s ORDER BY carga_id", (TIPO,)
    ).fetchall()


def test_carga_de_um_mes_publica_as_composicoes_e_a_api_enxerga(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao, banco_novo.conectar("rx_api") as api:
        relatorio = carregar(ingestao, mes_com((FUNDO_A, "250.00"), (FUNDO_B, "500.00")))

        assert (relatorio.fundos_no_arquivo, relatorio.gravados, relatorio.sem_mudanca) == (
            2,
            2,
            0,
        )
        vigentes = api.execute(
            "SELECT fundo_id, nome_fundo, data_referencia, moeda, patrimonio, fonte"
            " FROM ref.composicao_vigente ORDER BY fundo_id"
        ).fetchall()
        assert vigentes == sorted(
            (f"CNPJ:{f}", "FUNDO SINTETICO", date(2026, 8, 31), "BRL", D("1000.00"), FONTE)
            for f in (FUNDO_A, FUNDO_B)
        )
        itens = api.execute(
            "SELECT ativo_id, tipo, peso FROM ref.composicao_item_vigente WHERE fundo_id = %s",
            (f"CNPJ:{FUNDO_A}",),
        ).fetchall()
        assert itens == [(ACAO, "acao", D("0.25"))]
        (valor,) = ingestao.execute(
            "SELECT i.valor FROM ref.composicao_item i"
            " JOIN ref.composicao c USING (composicao_id) WHERE c.fundo_id = %s",
            (f"CNPJ:{FUNDO_A}",),
        ).fetchone()
        assert valor == D("250.00")  # o valor como a CVM informa, para auditar
        assert cargas(ingestao) == [("publicada", None)]


def test_mes_republicado_grava_so_os_fundos_que_mudaram_e_guarda_a_versao_anterior(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao, banco_novo.conectar("rx_api") as api:
        primeira = carregar(ingestao, mes_com((FUNDO_A, "250.00"), (FUNDO_B, "500.00")))

        segunda = carregar(ingestao, mes_com((FUNDO_A, "300.00"), (FUNDO_B, "500.00")))

        assert (segunda.gravados, segunda.sem_mudanca) == (1, 1)
        vigente = dict(
            api.execute("SELECT fundo_id, carga_id FROM ref.composicao_vigente").fetchall()
        )
        assert vigente == {
            f"CNPJ:{FUNDO_A}": segunda.carga_id,
            f"CNPJ:{FUNDO_B}": primeira.carga_id,
        }
        (versoes_de_a,) = ingestao.execute(
            "SELECT count(*) FROM ref.composicao WHERE fundo_id = %s", (f"CNPJ:{FUNDO_A}",)
        ).fetchone()
        assert versoes_de_a == 2


def test_mes_sem_mudanca_nao_abre_carga(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao:
        carregar(ingestao, mes_com((FUNDO_A, "250.00")))

        relatorio = carregar(ingestao, mes_com((FUNDO_A, "250.00")))

        assert (relatorio.carga_id, relatorio.gravados, relatorio.sem_mudanca) == (None, 0, 1)
        assert cargas(ingestao) == [("publicada", None)]


def test_arquivo_com_formato_novo_fica_com_erro_e_nada_e_publicado(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao:
        with pytest.raises(LayoutInesperado):
            carregar(ingestao, mes_com((FUNDO_A, "250.00")), sem=("fi_BLC_3",))

        ((status, motivo),) = cargas(ingestao)
        assert status == "com_erro"
        assert motivo.startswith("LayoutInesperado: arquivos fora do esperado")
        assert ingestao.execute("SELECT count(*) FROM ref.composicao").fetchone() == (0,)


def test_queda_grande_no_numero_de_fundos_do_mes_nao_publica(banco_novo):
    fundos = [(cnpj(f"QUEDA-{n}"), "100.00") for n in range(10)]
    with banco_novo.conectar("rx_ingestao") as ingestao:
        carregar(ingestao, mes_com(*fundos))

        with pytest.raises(ErroDeValidacao, match="5 fundos"):
            carregar(ingestao, mes_com(*fundos[:5]))

        assert [status for status, _ in cargas(ingestao)] == ["publicada", "com_erro"]


def test_cpf_nas_linhas_preparadas_impede_a_publicacao(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao:
        with pytest.raises(ErroDeValidacao):
            carregar(ingestao, mes_com((FUNDO_A, "250.00"), nome=f"FUNDO {CPF_DE_TESTE}"))

        ((status, motivo),) = cargas(ingestao)
        assert (status, CPF_DE_TESTE in motivo) == ("com_erro", False)
        assert ingestao.execute("SELECT count(*) FROM ref.composicao").fetchone() == (0,)


def test_motivo_do_cpf_aponta_o_fundo_sem_repetir_o_numero(banco_novo):
    with banco_novo.conectar("rx_ingestao") as ingestao:
        with pytest.raises(ErroDeValidacao):
            carregar(ingestao, mes_com((FUNDO_A, "250.00"), nome=f"FUNDO {CPF_DE_TESTE}"))

        ((_, motivo),) = cargas(ingestao)
        assert motivo == (
            "ErroDeValidacao: número com formato de CPF na coluna nome_fundo"
            f" (fundo_id CNPJ:{FUNDO_A})"
        )


def com_derivativo(lido: MesCDA) -> MesCDA:
    """O mês lido com um derivativo sobre a ACAO no fundo A. O leitor ainda não liga o derivativo
    ao ativo-objeto (DT-14): o teste o põe à mão, como a carga o receberá depois."""
    fundo = f"CNPJ:{FUNDO_A}"
    c = lido.composicoes[fundo]
    derivativo = ItemComposicao(None, D("0.01"), TipoItem.DERIVATIVO, ativo_objeto=ACAO)
    return replace(
        lido,
        composicoes={**lido.composicoes, fundo: replace(c, itens=(*c.itens, derivativo))},
        valores={**lido.valores, fundo: (*lido.valores[fundo], D("10.00"))},
    )


def test_ativo_objeto_e_gravado_e_o_mes_igual_nao_e_regravado(banco_novo, monkeypatch):
    # A assinatura do incremental compara o ativo_objeto: se ele não fosse gravado, todo fundo com
    # derivativo pareceria mudado a cada carga.
    monkeypatch.setattr(cvm, "ler_mes", lambda z: com_derivativo(ler_mes(z)))
    with banco_novo.conectar("rx_ingestao") as ingestao:
        carregar(ingestao, mes_com((FUNDO_A, "250.00")))

        segunda = carregar(ingestao, mes_com((FUNDO_A, "250.00")))

        assert (segunda.carga_id, segunda.gravados, segunda.sem_mudanca) == (None, 0, 1)
        gravado = ingestao.execute(
            "SELECT ativo_objeto FROM ref.composicao_item WHERE tipo = 'derivativo'"
        ).fetchall()
        assert gravado == [(ACAO,)]


def test_log_do_mes_com_erro_nao_repete_a_mensagem_da_excecao(
    banco_novo, monkeypatch, tmp_path, caplog
):
    def falhar(conexao, mes, obter_zip):
        raise ValueError("valor inválido: ZZMARCADOR")

    monkeypatch.setattr(cvm, "carregar_mes", falhar)
    monkeypatch.setenv("RX_BANCO_URL", banco_novo.url("rx_ingestao"))
    arquivo = tmp_path / "cda_fi_202608.zip"
    arquivo.write_bytes(b"")

    assert cvm.main(["--zip", str(arquivo)]) == 1

    assert "mês 202608: carga com erro (ValueError)" in caplog.text
    assert "ZZMARCADOR" not in caplog.text


def test_relatorio_lista_os_fundos_gravados_fora_de_1_por_cento(banco_novo):
    # O fundo B informa aplicações que somam metade do patrimônio.
    with banco_novo.conectar("rx_ingestao") as ingestao:
        relatorio = carregar(ingestao, mes_com((FUNDO_A, "1000.00"), (FUNDO_B, "500.00")))

        assert relatorio.fora_de_1_por_cento == [f"CNPJ:{FUNDO_B}"]
