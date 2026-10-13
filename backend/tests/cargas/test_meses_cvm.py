"""Escolha dos meses da carga da CVM, sem rede e sem banco."""

import pytest

from cargas.cvm import escolher_meses, mes_do_arquivo, meses_do_portal

# Trecho do índice do portal da CVM, com o formato da página (nginx autoindex) e nomes sintéticos.
INDICE = """
<a href="cda_fi_202607.zip">cda_fi_202607.zip</a> 12-Oct-2026 01:21 15M
<a href="cda_fi_202609.zip">cda_fi_202609.zip</a> 12-Oct-2026 01:07 9M
<a href="cda_fi_202608.zip">cda_fi_202608.zip</a> 12-Oct-2026 01:14 15M
<a href="cda_fi_202606.zip">cda_fi_202606.zip</a> 10-Oct-2026 06:34 26M
<a href="meta_cda_fi.txt">meta_cda_fi.txt</a>
<a href="cda_fi_202609.zip">cda_fi_202609.zip</a>
"""


def test_le_os_meses_do_indice_do_portal_do_mais_recente_para_o_mais_antigo():
    assert meses_do_portal(INDICE) == ["202609", "202608", "202607", "202606"]


def test_indice_sem_nenhum_mes_e_erro():
    with pytest.raises(ValueError, match="nenhum mês"):
        meses_do_portal("<html>página em manutenção</html>")


def test_escolhe_os_meses_recentes():
    meses = ["202609", "202608", "202607", "202606", "202605"]

    assert escolher_meses(meses, quantidade=3) == ["202609", "202608", "202607"]
    # A carga semanal pula os 3 recentes, que já rodam de terça a sábado.
    assert escolher_meses(meses, quantidade=9, pular=3) == ["202606", "202605"]


def test_mes_do_arquivo_segue_o_nome_do_portal():
    assert mes_do_arquivo("dados/cda_fi_202608.zip") == "202608"
    with pytest.raises(ValueError, match="cda_fi_AAAAMM.zip"):
        mes_do_arquivo("agosto.zip")
