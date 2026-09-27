"""XML malicioso: entidades não podem ser expandidas nem ler arquivos locais."""

import pytest
from lxml import etree

from ingest.nport import parse_nport
from ingest.sec_edgar import parse_segmentos_instancia
from ingest.xml_seguro import ler_xml

NPORT_COM_ENTIDADE = b"""<?xml version="1.0"?>
<!DOCTYPE edgarSubmission [<!ENTITY injetada "TEXTO_INJETADO">]>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">
  <formData>
    <genInfo><seriesId>S000000001</seriesId></genInfo>
    <invstOrSecs>
      <invstOrSec><name>&injetada;</name><cusip>000000AA1</cusip>
        <valUSD>1.0</valUSD><pctVal>1.0</pctVal></invstOrSec>
    </invstOrSecs>
  </formData>
</edgarSubmission>"""

BILLION_LAUGHS = b"""<?xml version="1.0"?>
<!DOCTYPE bomba [
  <!ENTITY a "aaaaaaaaaa">
  <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">
  <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">
  <!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;&c;&c;">
  <!ENTITY e "&d;&d;&d;&d;&d;&d;&d;&d;&d;&d;">
]>
<bomba>&e;</bomba>"""


def test_entidade_declarada_no_arquivo_nao_e_expandida():
    raiz = ler_xml(NPORT_COM_ENTIDADE)

    assert b"TEXTO_INJETADO" not in etree.tostring(raiz)


def test_leitor_do_nport_nao_expande_entidades():
    _, posicoes = parse_nport(NPORT_COM_ENTIDADE)

    assert not posicoes["name"].fillna("").str.contains("TEXTO_INJETADO").any()


def test_billion_laughs_nao_explode_a_memoria():
    try:
        raiz = ler_xml(BILLION_LAUGHS)
    except etree.XMLSyntaxError:
        return  # recusar o arquivo também é aceitável
    assert len(etree.tostring(raiz)) < 10_000


def test_entidade_externa_nao_le_arquivo_local(tmp_path):
    segredo = tmp_path / "segredo.txt"
    segredo.write_text("CONTEUDO_SECRETO", encoding="utf-8")
    xml = (
        f'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY ext SYSTEM "{segredo.as_uri()}">]><x>&ext;</x>'
    ).encode()

    try:
        raiz = ler_xml(xml)
    except etree.XMLSyntaxError:
        return
    assert b"CONTEUDO_SECRETO" not in etree.tostring(raiz)


@pytest.mark.parametrize("leitor", [parse_segmentos_instancia])
def test_leitor_do_xbrl_aceita_xml_com_entidade_sem_expandir(leitor):
    xml = (
        b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY injetada "TEXTO_INJETADO">]>'
        b'<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance">&injetada;</xbrli:xbrl>'
    )

    assert leitor(xml).empty
