# Backend — comandos e regras (rodar dentro de backend/)

## Ambiente
Python 3.14 com venv + pip. Não usar uv, poetry nem pip fora do venv.

## Comandos
- py -3.14 -m venv .venv                      cria o ambiente (uma vez)
- source .venv/Scripts/activate               Git Bash no Windows (no Linux/CI: .venv/bin/activate)
- python -m pip install -r requirements-dev.txt
- python -m pytest                            testes (Hypothesis incluso)
- python -m ruff check . && python -m ruff format --check .
- uvicorn app.main:app --reload               servidor local
- python -m app.exportar_openapi              gera ../frontend/openapi.json
- pip-audit -r requirements.txt               auditoria de dependências

## Dependências
- requirements.txt: só produção (fastapi, pydantic, uvicorn...), versões fixas com ==.
- requirements-dev.txt: começa com "-r requirements.txt" e adiciona pytest, hypothesis,
  httpx, ruff e pip-audit, também com ==.
- pyproject.toml guarda só a configuração do ruff (target-version = "py314") e do pytest;
  não lista dependências.
- Dependência nova: adicionar no arquivo certo, instalar, rodar os testes e commitar junto.

## Regras
- yfinance é proibido (bloqueado no ruff por flake8-tidy-imports.banned-api).
- app/core/ é puro: sem FastAPI, sem banco, sem rede. O I/O fica em app/api/ e ingest/.
- Valores em dinheiro e pesos usam Decimal, nunca float.
- ISIN validado com dígito verificador em core/identificadores.
- POST /raiox não grava nem registra em log o conteúdo da carteira.
- Caminhos com pathlib; todo open() com encoding explícito.
- tests/fixtures/ só com dados sintéticos. Use Hypothesis para invariantes
  (por exemplo: a soma das exposições é igual ao total, o look-through termina mesmo com ciclo).
- Reaproveitamento do tracker.py: portar função por função, com o teste antes.
  Nada que dependa de yfinance ou de rentabilidade.
- ingest/ SEC: User-Agent declarado e no máximo 10 req/s. ingest/ CVM: registrar o crédito ODbL
  para aparecer em GET /fontes.
