"""Esquema do snapshot que gera o tipo do front (frontend/src/vitrine/tipos.ts)."""

import json

from vitrine.exportar_esquema import esquema, exportar


def test_esquema_tem_o_snapshot_e_sai_igual_toda_vez():
    a, b = esquema(), esquema()

    assert "Snapshot" in a["components"]["schemas"]
    assert json.dumps(a) == json.dumps(b)


def test_fracao_e_documentada_como_numero():
    # Pesos são Decimal no backend, mas o JSON gravado traz número: o tipo do front diz number.
    empresa = esquema()["components"]["schemas"]["Empresa"]["properties"]

    assert empresa["peso_efetivo"]["type"] == "number"


def test_referencias_apontam_para_os_componentes():
    texto = json.dumps(esquema())

    assert "#/$defs/" not in texto
    assert "#/components/schemas/Carteira" in texto


def test_exporta_em_utf8_com_quebra_de_linha_final(tmp_path):
    saida = tmp_path / "snapshot.openapi.json"

    exportar(saida)

    texto = saida.read_text(encoding="utf-8")
    assert json.loads(texto) == esquema()
    assert texto.endswith("}\n")
