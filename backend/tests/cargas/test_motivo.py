"""O motivo de uma carga com erro (ref.carga.motivo_erro e o log) nunca leva valores das linhas.

O erro do banco tem o seu teste em tests/banco/test_rotina_carga.py, que precisa do PostgreSQL.
"""

import pytest

from cargas.baixar import ErroDeDownload
from cargas.cadastro import _mais_recentes
from cargas.cvm import meses_do_portal
from cargas.identificacao import CuradoriaInvalida
from cargas.rotina import CargaEmAndamento, ErroDeValidacao, motivo
from ingest.arquivos_cvm import LayoutInesperado

MARCADOR = "ZZMARCADOR"  # valor sintético fácil de procurar no motivo


@pytest.mark.parametrize(
    "erro",
    [
        ErroDeValidacao("a foto nova tem 5 ativos; a vigente tem 10"),
        LayoutInesperado("falta o arquivo cda_fi_PL_202608.csv"),
        CargaEmAndamento("outra carga do tipo ptax está rodando"),
        ErroDeDownload("arquivo maior que 10 bytes"),
        CuradoriaInvalida("emissores_b3.csv, linha 2: CNPJ inválido"),
    ],
)
def test_excecao_do_projeto_mantem_a_mensagem_que_o_codigo_escreveu(erro):
    assert motivo(erro) == f"{type(erro).__name__}: {erro}"


@pytest.mark.parametrize(
    "erro",
    [
        ValueError(f"valor inválido: {MARCADOR}"),
        KeyError(MARCADOR),
        ConnectionError(f"{MARCADOR} fora do ar"),
    ],
)
def test_outra_excecao_fica_so_com_o_nome_da_classe(erro):
    assert motivo(erro) == type(erro).__name__


def test_indice_do_portal_sem_arquivos_e_formato_inesperado_com_a_mensagem():
    # Um índice sem nenhum arquivo é mudança no portal: a mensagem fica no motivo.
    with pytest.raises(LayoutInesperado, match="nenhum mês"):
        meses_do_portal("<html>página em manutenção</html>")
    with pytest.raises(LayoutInesperado, match="nenhum arquivo"):
        _mais_recentes("<html>página em manutenção</html>", r"fca_cia_aberta_\d{4}\.zip", 3)


def test_curadoria_errada_e_erro_de_validacao(tmp_path):
    from cargas.identificacao import ler_curadoria

    (tmp_path / "emissores_b3.csv").write_text("raiz;cnpj;nome;motivo\n1ABC;x;y;z\n", "utf-8")
    (tmp_path / "fundos_listados.csv").write_text("ticker;cnpj;nome;fonte\n", encoding="utf-8")

    with pytest.raises(ErroDeValidacao, match="emissores_b3.csv, linha 2"):
        ler_curadoria(tmp_path)
