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
  RepositorioDados) e a PTAX (FonteCambio, em app/dados/ptax.py). Com RX_BANCO_URL, a PTAX vem
  da ref.ptax_vigente (FontePtaxBanco), gravada pela carga diária, e a API não chama o Banco
  Central; sem ela, a FontePtax busca no Banco Central, com cache. Com RX_BANCO_URL a API usa o
  RepositorioPostgres (app/dados/postgres.py): lê as visões vigentes como rx_api, guarda uma foto em
  memória e só relê quando sai carga nova (DT-10), sem travar as análises: um pedido só relê,
  fora da trava, e os outros seguem com a foto anterior. Nada roda em segundo plano (no Cloud
  Run não há CPU fora dos pedidos): relê um pedido, a partida do servidor ou o aquecimento
  interno (POST /interno/aquecer, fora do /api, com o segredo no cabeçalho x-rx-aquecimento;
  sem ele, 404). Sem RX_BANCO_URL, usa o RepositorioExemplo,
  sintético. Cada análise pede uma foto só (FonteDados.foto(), em app.state.dados), para não
  misturar dois momentos do banco.
  Testes da API trocam repositório e PTAX por app.dependency_overrides; nenhum teste usa rede.
- Valores em dinheiro e pesos usam Decimal, nunca float.
- A carteira entra por identificador e tipo_identificador (isin, ticker_b3, ticker_eua ou cnpj; ADR
  0005, seção 5), validados em core/identificadores (ISIN e CNPJ com dígito verificador; ISIN só de
  país da lista permitida) e traduzidos para o ativo_id em core/traducao, pela identificação da foto.
  Para ativo conhecido, vale o tipo da identificação, não o declarado; quando eles divergem, a
  resposta traz o aviso tipo_corrigido, com o índice da posição (posicao) e o tipo usado, sem
  repetir o identificador.
- POST /api/raiox não grava nem registra em log o conteúdo da carteira. Respostas de erro também
  não repetem a entrada: 422 traz só campo, motivo e mensagem; exceção inesperada vira 500
  genérico e o log guarda só o tipo e o arquivo:linha (app/api/erros.py).
- Valores em dinheiro trafegam como texto ("1000.00"), nunca como número JSON.
- Caminhos com pathlib; todo open() com encoding explícito.
- tests/fixtures/ só com dados sintéticos. Use Hypothesis para invariantes
  (por exemplo: a soma das exposições é igual ao total, o look-through termina mesmo com ciclo).
- Reaproveitamento do tracker.py: portar função por função, com o teste antes.
  Nada que dependa de yfinance ou de rentabilidade.
- ingest/ SEC: User-Agent declarado e no máximo 10 req/s. ingest/ CVM: registrar o crédito ODbL
  para aparecer em GET /api/fontes.
- Todo XML externo passa por ingest/xml_seguro.ler_xml (nunca etree.fromstring direto).

## Banco: PostgreSQL (ver ADR 0006)
Comandos dentro de backend/, com o Docker Desktop aberto:
- docker compose up -d --wait                 sobe o PostgreSQL de desenvolvimento (127.0.0.1:5433)
- export RX_BANCO_URL_ADMIN=postgresql+psycopg://postgres@127.0.0.1:5433/postgres
  python -m banco.preparar                    cria os usuários e o banco rx (uma vez)
- export RX_BANCO_URL=postgresql+psycopg://rx_dono@127.0.0.1:5433/rx
  python -m alembic upgrade head              aplica as migrações (só como rx_dono)
- export RX_BANCO_TESTE_URL=postgresql+psycopg://postgres@127.0.0.1:5433/postgres
  python -m pytest tests/banco                testes com banco; sem a variável, são pulados
- docker compose down                         para o banco (os dados ficam no volume; -v apaga)
O PostgreSQL do compose aceita conexão sem senha e só escuta em 127.0.0.1: serve só para
desenvolvimento e CI (job "banco"). A porta é a 5433 para não brigar com um PostgreSQL local.
Regras:
- banco/preparar.py só cria os usuários e o banco. Tudo dentro do banco (esquemas, tabelas, visões e
  permissões) vem das migrações, em banco/migracoes/versions/.
- Migrações só para frente (downgrade levanta erro): um erro se corrige com uma migração nova.
  Escritas em SQL à mão e revisadas no PR. Nova migração:
    python -m alembic revision -m "descrição curta" --rev-id 0002   (número seguinte)
- Esquemas: ref (dados públicos) e app (lista de espera e a versão das migrações). O public fica
  sem uso e sem permissão.
- Toda tabela, visão ou função nova diz, na mesma migração, quem pode o quê (GRANT), com teste em
  tests/banco. Valores e pesos em NUMERIC, nunca real nem double precision.
- Dados de ref só entram por carga: abrir a carga (nasce "carregando"), inserir as linhas e
  publicar numa transação só. Linha só entra em carga aberta do tipo certo; carga publicada não muda;
  ninguém além do rx_dono altera ou apaga linhas (gatilhos e permissões da migração 0002).
- A API lê só as visões *_vigente e carga_publicada, nunca as tabelas.
- Identificadores nas colunas com os domínios ref.ativo_id, ref.empresa_id e ref.isin_permitido:
  o próprio banco recusa CUSIP, SEDOL e ISIN de país fora da lista do ADR 0005.

## Lote: ingest/ e irrae/ (ver ADR 0004)
- ingest/: leitores de dados externos, compartilhados pelo produto e pelo IrRAE.
- irrae/: modelo do M1 (dono da metodologia). Configurações em irrae/config/.
  Mudança de regra ou mapeamento é decisão do M1; a lista de decisões conjuntas está no ADR 0004.
- Rodam em lote, fora da API. app/ nunca importa irrae/.
- Dentro de irrae/ o uso de float e numpy é permitido; o resultado vira Decimal ao ser gravado.
- Dependências: requirements-lote.in/.txt (CI) e requirements-analise.in/.txt (opcional).
    python -m pip install --require-hashes -r requirements-dev.txt -r requirements-lote.txt
    python -m pytest tests/ingest tests/irrae     (no CI: job "lote")

## Cargas: cargas/ (ver ADR 0006, seção 5, e ADR 0008)
- Jobs em lote que gravam os dados públicos no banco, como rx_ingestao. Só dependências de
  produção (requirements.txt): os leitores que usam (ex.: ingest/cvm_cda.py) não podem importar
  pandas nem lxml.
- cargas/rotina.py: o caminho comum (trava por tipo, carga parada vira com_erro, gravação e
  publicação numa transação só). Toda carga nova usa publicar_carga e registrar_falha.
- Nenhum arquivo bruto é guardado: o download fica só na memória (cargas/baixar.py, só https e só
  o endereço da fonte). Antes de publicar, a varredura de CPF (cargas/validacao.py).
- CVM (CDA), carga incremental (só os fundos que mudaram):
    export RX_BANCO_URL=postgresql+psycopg://rx_ingestao@127.0.0.1:5433/rx
    python -m cargas.cvm                        os 3 meses mais recentes
    python -m cargas.cvm --pular 3 --meses 9    os 9 meses seguintes (semanal)
    python -m cargas.cvm --zip cda_fi_AAAAMM.zip    um zip local
- Cadastro (ADR 0008, etapa 4): identificação (empresas, ações pelo ISIN ou pelo código interno
  B3:, ETFs e FIIs) e setor oficial, a partir do FCA, do CDA e do informe de FII, mais a curadoria
  manual em cargas/curadoria/ (README lá dentro). Foto completa a cada carga, toda segunda:
    python -m cargas.cadastro                   baixa as fontes do portal da CVM
    python -m cargas.cadastro --pasta DIR       lê os zips já baixados (nomes do portal)
- Leitores da CVM (ingest/): cvm_cda.py, cvm_fca.py e cvm_fii.py, com o que é comum em
  arquivos_cvm.py. Só stdlib, para rodarem na imagem de produção.
- PTAX (fonte 12 da matriz), dias úteis às 13h30 e às 18h (ADR 0007, seção 5): os últimos 15
  dias, gravando só as datas novas ou corrigidas; variação de mais de 10% sobre o dia útil
  anterior trava a carga:
    python -m cargas.ptax                       os últimos 15 dias
    python -m cargas.ptax --dias 60             uma janela maior (primeira carga)
- Testes: tests/cargas (sem banco, job "backend") e tests/banco/test_rotina_carga.py,
  test_carga_cvm.py, test_carga_cadastro.py e test_carga_ptax.py (com banco, job "banco").
- Medição da foto da API (DT-10), com o banco carregado e RX_BANCO_URL do rx_api:
    python -m medicoes.foto_dos_dados
- Pico de memória de uma carga (ADR 0007, seção 5). Publica de verdade: só aceita RX_BANCO_URL do
  banco local (127.0.0.1 ou localhost), com o rx_ingestao:
    python -m medicoes.pico_da_carga cadastro [--pasta DIR]
    python -m medicoes.pico_da_carga cvm --meses 3

## API: limites e configuração
- Limites (app/api/raiox.py, esquemas.py e main.py): 500 posições, das quais até 100 fundos;
  200 empresas na resposta (o resto somado em demais_empresas); 20 análises por minuto por IP
  (429); 4 análises simultâneas por servidor (503); corpo de até 1 MB (413).
- Banco fora do ar antes da primeira leitura: 503 dados_indisponiveis (conexão espera até 5 s).
  Depois da primeira leitura, a API segue com a última foto.
- Contadores em memória, por servidor (DT-2 em docs/divida_tecnica.md).
- IP do limite (app/api/seguranca.py, chave_do_limite; DT-17): o N-ésimo endereço da direita do
  X-Forwarded-For, com N = RX_PROXIES_CONFIAVEIS; o IP da conexão com N = 0, com endereços de
  menos ou com valor que não é IP. IPv6 conta pela rede /64. Quem lê o cabeçalho é a aplicação.
- GET /interno/ip-do-cliente (app/api/interno.py; DT-17): com o segredo do aquecimento no
  x-rx-aquecimento, devolve os endereços do X-Forwarded-For e a chave do limite, sem log; sem o
  segredo, 404. Serve para medir a posição no primeiro deploy (ADR 0007, seção 3).
- Configuração pelas variáveis de ambiente do processo (app/config.py):
    RX_AMBIENTE=desenvolvimento|producao   produção desliga /docs, /redoc e /openapi.json e liga o HSTS
    RX_ORIGENS_PERMITIDAS=https://...       origens do front no CORS, separadas por vírgula
    RX_BANCO_URL=postgresql+psycopg://rx_api@...   banco (ADR 0006); sem ela, dados de exemplo;
                                            obrigatória em produção; nunca em log nem em mensagem
    RX_SEGREDO_AQUECIMENTO=...              segredo do aquecimento interno (32+ caracteres); sem
                                            ele, o aquecimento responde 404
    RX_PROXIES_CONFIAVEIS=0..5              quantos proxies acrescentam endereço ao X-Forwarded-For
                                            (DT-17); sem ela, 0 (o IP da conexão); obrigatória
                                            em produção
  Valor inválido derruba o servidor na partida, de propósito.
- Produção: o comando da imagem (Dockerfile), uvicorn app.main:app --host 0.0.0.0 --port 8080
  --no-server-header --no-proxy-headers --no-access-log. O uvicorn não mexe no IP da conexão:
  quem lê o X-Forwarded-For é a aplicação, com RX_PROXIES_CONFIAVEIS (DT-17). Nunca use
  --forwarded-allow-ips="*" sem um proxy que sobrescreva o X-Forwarded-For. Sem log de acesso: o
  Cloud Run já registra cada pedido, com o IP.

## Imagem: Dockerfile (ver ADR 0007)
Uma imagem para a API, as cargas e as migrações (Cloud Run e Cloud Run Jobs), com um comando para
cada uma. Leva só o requirements.txt e o código de app/, banco/, cargas/ e ingest/ (.dockerignore);
roda com o usuário rx, sem root e sem escrita no código. Comandos dentro de backend/, com o Docker
aberto:
- docker build -t rx-backend .
- scripts/testar_imagem.sh [IMAGEM]           com o venv ativo: constrói (ou usa a IMAGEM dada) e
                                              testa o conteúdo, as migrações, a carga da CVM com zip
                                              sintético e a API em produção lendo o banco, num
                                              PostgreSQL descartável (no CI: job "imagem")
- Jobs: python -m alembic upgrade head (como rx_dono); python -m cargas.cvm, cargas.cadastro e
  cargas.ptax (como rx_ingestao).
- Python e Debian fixados pelo digest. O Dependabot propõe as correções (3.14.x); a troca de versão
  (3.15) é à mão, junto com o CI e o target-version do ruff.
- pip com CERTIFICATE_VERIFY_FAILED no docker build: um antivírus está inspecionando o HTTPS da
  máquina. Libere pypi.org e files.pythonhosted.org na inspeção; não mude o Dockerfile por isso.
