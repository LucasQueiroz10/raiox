# Backend — comandos e regras (rodar dentro de backend/)

## Ambiente
Python 3.14 com venv + pip. Não usar uv, poetry nem pip fora do venv.

## Comandos
- py -3.14 -m venv .venv                      cria o ambiente (uma vez)
- source .venv/Scripts/activate               Git Bash no Windows (no Linux/CI: .venv/bin/activate)
- python -m pip install --require-hashes -r requirements-dev.txt
- python -m pytest                            testes (Hypothesis incluso)
- python -m ruff check . && python -m ruff format --check .
- uvicorn app.main:app --reload               servidor local
- python -m app.exportar_openapi              gera ../frontend/openapi.json
- pip-audit --require-hashes --disable-pip -r requirements.txt   auditoria de dependências

## Dependências (travadas com hash pelo pip-tools)
- requirements.in: dependências diretas de produção (fastapi, pydantic, uvicorn...), com ==.
- requirements-dev.in: ferramentas de desenvolvimento, presas às versões de produção.
- requirements.txt e requirements-dev.txt são GERADOS (todas as dependências, inclusive as
  indiretas, com versão exata e hash). Nunca editar à mão:
    python -m piptools compile --generate-hashes --strip-extras -o requirements.txt requirements.in
    python -m piptools compile --generate-hashes --strip-extras --allow-unsafe -o requirements-dev.txt requirements-dev.in
- Dependência nova: adicionar no .in certo, gerar os .txt, instalar, rodar os testes e commitar
  os quatro arquivos juntos.
- pyproject.toml guarda só a configuração do ruff (target-version = "py314") e do pytest;
  não lista dependências.
- Regras de segurança do ruff (S, flake8-bandit) ativas; nos testes só o assert é liberado.

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
- Todo XML externo passa por ingest/xml_seguro.ler_xml (nunca etree.fromstring direto).

## Lote: ingest/ e irrae/ (ver ADR 0004)
- ingest/: leitores de dados externos, compartilhados pelo produto e pelo IrRAE.
- irrae/: modelo do M1 (dono da metodologia). Configurações em irrae/config/.
  Mudança de regra ou mapeamento é decisão do M1; a lista de decisões conjuntas está no ADR 0004.
- Rodam em lote, fora da API. app/ nunca importa irrae/.
- Dentro de irrae/ o uso de float e numpy é permitido; o resultado vira Decimal ao ser gravado.
- Dependências: requirements-lote.in/.txt (CI) e requirements-analise.in/.txt (opcional).
    python -m pip install --require-hashes -r requirements-dev.txt -r requirements-lote.txt
    python -m pytest tests/ingest tests/irrae     (no CI: job "lote")
