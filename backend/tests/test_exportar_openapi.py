"""O contrato da API (OpenAPI) que gera os tipos do front (frontend/src/api/tipos.ts)."""

import json

from app.exportar_openapi import esquema, exportar


def test_esquema_tem_as_rotas_e_sai_igual_toda_vez():
    a, b = esquema(), esquema()

    assert {"/api/raiox", "/api/saude"} <= set(a["paths"])
    assert json.dumps(a) == json.dumps(b)


def test_valor_de_entrada_e_documentado_como_texto():
    # A API recusa número JSON (passaria pelo float); o tipo gerado no front precisa dizer string.
    valor = esquema()["components"]["schemas"]["PosicaoEntrada"]["properties"]["valor"]

    assert valor["type"] == "string"
    assert "anyOf" not in valor


def test_exporta_em_utf8_com_quebra_de_linha_final(tmp_path):
    saida = tmp_path / "openapi.json"

    exportar(saida)

    texto = saida.read_text(encoding="utf-8")
    assert json.loads(texto) == esquema()
    assert texto.endswith("}\n")
