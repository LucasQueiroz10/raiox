"""Hook PostToolUse (Edit|Write): formata o arquivo que o Claude acabou de editar.

- .py dentro de backend/  -> ruff format, com o Python do venv do backend
- arquivos de frontend/   -> prettier --write --ignore-unknown, com o Prettier do projeto
Qualquer outro arquivo é ignorado. Nunca bloqueia a edição: sai sempre com código 0.
"""

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BACKEND = RAIZ / "backend"
FRONTEND = RAIZ / "frontend"


def _python_do_venv() -> Path | None:
    for candidato in (
        BACKEND / ".venv" / "Scripts" / "python.exe",
        BACKEND / ".venv" / "bin" / "python",
    ):
        if candidato.is_file():
            return candidato
    return None


def _dentro(caminho: Path, pasta: Path) -> bool:
    return caminho.is_relative_to(pasta)


def comando_para(caminho: Path) -> tuple[list[str], Path] | None:
    """Comando de formatação e pasta de trabalho, ou None se o arquivo não se aplica."""
    if _dentro(caminho, BACKEND / ".venv") or _dentro(
        caminho, FRONTEND / "node_modules"
    ):
        return None
    if _dentro(caminho, BACKEND) and caminho.suffix == ".py":
        python = _python_do_venv()
        if python:
            return [str(python), "-m", "ruff", "format", str(caminho)], BACKEND
    if _dentro(caminho, FRONTEND):
        prettier = FRONTEND / "node_modules" / "prettier" / "bin" / "prettier.cjs"
        if prettier.is_file():
            return [
                "node",
                str(prettier),
                "--write",
                "--ignore-unknown",
                str(caminho),
            ], FRONTEND
    return None


def main() -> None:
    try:
        entrada = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        bruto = (entrada.get("tool_response") or {}).get("filePath") or (
            entrada.get("tool_input") or {}
        ).get("file_path")
        if not bruto:
            return
        caminho = Path(bruto).resolve()
        if not caminho.is_file():
            return
        comando = comando_para(caminho)
        if comando:
            args, pasta = comando
            subprocess.run(
                args, cwd=pasta, capture_output=True, timeout=60, check=False
            )
    except Exception:  # noqa: BLE001 - formatar é conveniência; nunca atrapalha a edição
        return


if __name__ == "__main__":
    main()
