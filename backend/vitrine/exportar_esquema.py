"""Exporta o esquema do snapshot para o front gerar o tipo (ADR 0009, seção 2).

Uso (de dentro de backend/): python -m vitrine.exportar_esquema
Grava ../frontend/snapshot.openapi.json; depois, no front: npm run gerar-tipos-snapshot. O esquema
vai embrulhado num documento OpenAPI para o openapi-typescript, que o front já usa para a API,
gerar o tipo sem dependência nova. O CI confere que os dois arquivos commitados batem com o modelo.
"""

import json
import sys
from pathlib import Path

from vitrine.snapshot import Snapshot

SAIDA_PADRAO = Path(__file__).resolve().parents[2] / "frontend" / "snapshot.openapi.json"


def esquema() -> dict:
    # Modo "serialization": o tipo descreve o JSON gravado (frações como número), não a entrada.
    schema = Snapshot.model_json_schema(
        mode="serialization", ref_template="#/components/schemas/{model}"
    )
    componentes = schema.pop("$defs", {})
    componentes["Snapshot"] = schema
    return {
        "openapi": "3.1.0",
        "info": {"title": "Snapshot da vitrine da Sagital", "version": "1"},
        "paths": {},
        "components": {"schemas": componentes},
    }


def exportar(saida: Path = SAIDA_PADRAO) -> None:
    texto = json.dumps(esquema(), indent=2, ensure_ascii=False) + "\n"
    Path(saida).write_text(texto, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    exportar(Path(sys.argv[1]) if len(sys.argv) > 1 else SAIDA_PADRAO)
