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
- python -m app.exportar_openapi              gera ../frontend/openapi.json (depois: npm run gerar-tipos no front)
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
- app/core/ é puro: sem FastAPI, sem banco, sem rede. O I/O fica em app/api/, app/dados/ e ingest/.
- app/dados/: de onde vêm composições, ligação ativo -> empresa, classificação e nomes (protocolo
  RepositorioDados) e a PTAX (FontePtax, com cache). Até o banco existir, a API usa
  RepositorioExemplo, sintético.
  Testes da API trocam repositório e PTAX por app.dependency_overrides; nenhum teste usa rede.
- Valores em dinheiro e pesos usam Decimal, nunca float.
- ISIN validado com dígito verificador em core/identificadores.
- POST /raiox não grava nem registra em log o conteúdo da carteira. Respostas de erro também
  não repetem a entrada: 422 traz só campo, motivo e mensagem; exceção inesperada vira 500
  genérico e o log guarda só o tipo e o arquivo:linha (app/api/erros.py).
- Valores em dinheiro trafegam como texto ("1000.00"), nunca como número JSON.
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

## API: limites e configuração
- Limites (app/api/raiox.py, esquemas.py e main.py): 500 posições, das quais até 100 fundos;
  200 empresas na resposta (o resto somado em demais_empresas); 20 análises por minuto por IP
  (429); 4 análises simultâneas por servidor (503); corpo de até 1 MB (413).
- Contadores em memória, por servidor (DT-2 em docs/divida_tecnica.md).
- Configuração pelas variáveis de ambiente do processo (app/config.py):
    RX_AMBIENTE=desenvolvimento|producao   produção desliga /docs, /redoc e /openapi.json e liga o HSTS
    RX_ORIGENS_PERMITIDAS=https://...       origens do front no CORS, separadas por vírgula
  Valor inválido derruba o servidor na partida, de propósito.
- Produção: uvicorn app.main:app --no-server-header --forwarded-allow-ips=<IP do proxy>
  O IP do limite é o da conexão; o uvicorn só aceita o X-Forwarded-For vindo desses IPs.
  Nunca use --forwarded-allow-ips="*" sem um proxy que sobrescreva o X-Forwarded-For.
