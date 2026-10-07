"""Exporta o contrato da API (OpenAPI) para o front gerar os tipos.

Uso (de dentro de backend/): python -m app.exportar_openapi
Grava ../frontend/openapi.json; depois, no front: npm run gerar-tipos. O CI confere que os dois
arquivos commitados batem com o código.
"""

import json
import sys
from pathlib import Path

from app.config import Config
from app.main import criar_app

SAIDA_PADRAO = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def esquema() -> dict:
    # Configuração fixa: o contrato não pode depender das variáveis de ambiente de quem exporta.
    return criar_app(Config(producao=False, origens_permitidas=())).openapi()


def exportar(saida: Path = SAIDA_PADRAO) -> None:
    texto = json.dumps(esquema(), indent=2, ensure_ascii=False) + "\n"
    Path(saida).write_text(texto, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    exportar(Path(sys.argv[1]) if len(sys.argv) > 1 else SAIDA_PADRAO)
