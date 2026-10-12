# ADR 0007: Hospedagem no Google Cloud

- **Status:** proposto
- **Data:** 2026-10-12
- **Decisor:** Lucas (Membro 2), por ser decisão de engenharia (ADR 0004). O M1 revisa a região dos
  dados, os logs e a retenção (LGPD e Marco Civil da Internet) e o custo.
- **Relacionados:** ADR 0003 (stack), ADR 0006 (banco de dados), DT-1, DT-2, DT-4 e DT-10.
- **Fora do escopo:** a fase com contas de usuário (ADR próprio) e a proteção de borda avançada
  (Cloud Armor), prevista para depois do P3.

## Contexto

O portão P3 (23/10/2026) pede um ambiente com HTTPS para o teste fechado. O sistema tem cinco peças:
o front (React, arquivos estáticos), a API (FastAPI, num contêiner), o banco (PostgreSQL), as cargas
em lote (CVM, FCA e PTAX; depois, as da SEC) e as migrações. A equipe é pequena, então a preferência
é por serviços gerenciados, pagos pelo uso. Os dados ficam no Brasil sempre que possível (LGPD e
latência para o usuário).

## Decisões

### 1. Provedor e região

- **Google Cloud, região `southamerica-east1` (São Paulo)**, para tudo o que guarda ou processa
  dados: API, banco, cargas, imagens, segredos e logs.
- A única peça global é a rede de entrega do front (arquivos estáticos, sem dado de usuário).
- Um projeto de produção no P3. Um ambiente de homologação vem depois (seção 10).

### 2. As peças

| Peça | Serviço | Observação |
|---|---|---|
| Front (React) | Firebase Hosting | Rede de entrega global, HTTPS e domínio próprio sem custo fixo |
| API (FastAPI) | Cloud Run (serviço) | O Firebase encaminha `/api/**` para ela: mesmo endereço do front, sem CORS |
| Banco | Cloud SQL for PostgreSQL 17 | Mesma versão do desenvolvimento e do CI (17.11) |
| Cargas | Cloud Run Jobs com Cloud Scheduler | Mesma imagem da API, outro comando; horários de Brasília |
| Migrações | Cloud Run Job `migrar` | Roda como `rx_dono` em cada deploy, depois de um backup |
| Imagens | Artifact Registry (São Paulo) | Construídas no GitHub Actions |
| Segredos | Secret Manager | Os endereços do banco, com senha, um por usuário |
| Logs e alertas | Cloud Logging e Cloud Monitoring | Seção 8 |

O Firebase Hosting aceita encaminhar para o Cloud Run em `southamerica-east1` (lista de regiões da
documentação do Firebase, conferida em 12/10/2026).

### 3. API no Cloud Run

- **Instâncias:** mínimo de 1 durante o P3, para a primeira análise não esperar a partida do
  contêiner nem a leitura da foto dos dados (DT-10); máximo de 3, por custo e porque o limite por IP
  é contado em cada instância (DT-2).
- **Análises por instância:** 4, o mesmo `MAX_ANALISES_SIMULTANEAS` da API. O cálculo usa CPU e o
  Python faz um por vez; com a fila cheia, o Cloud Run sobe outra instância. É a opção C da DT-4.
- **CPU e memória:** 1 vCPU e 2 GiB para começar (a foto dos dados mais 4 análises de uns 60 MB).
  Medir com a primeira carga completa da CVM (DT-10).
- **Configuração:** `RX_AMBIENTE=producao`; `RX_BANCO_URL` vem do Secret Manager (usuário `rx_api`);
  `RX_ORIGENS_PERMITIDAS` vazio, porque o front e a API ficam no mesmo endereço.
- **IP do cliente para o limite por IP:** no Cloud Run a conexão chega da infraestrutura do Google,
  e o IP do cliente vem no cabeçalho `X-Forwarded-For`. O primeiro endereço desse cabeçalho pode ser
  forjado pelo próprio cliente. Decisão: usar o endereço que a infraestrutura do Google acrescenta,
  nunca o primeiro. A posição exata é conferida no primeiro deploy, com uma requisição nossa. Nunca
  `--forwarded-allow-ips="*"` sem esse tratamento (`backend/CLAUDE.md`).
- **Tempo por requisição:** o encaminhamento do Firebase tem limite de 60 s; o pior caso da análise
  fica em uns 2 s (DT-4).

### 4. Banco no Cloud SQL

- **PostgreSQL 17**, edição Enterprise. O Cloud SQL já oferece o 18, mas o 17 é a versão testada no
  desenvolvimento e no CI e tem suporte regular até 01/02/2030. A troca para o 18 vem com teste, por
  migração própria.
- **Tamanho:** começar pequeno e medir com a primeira carga completa da CVM (cerca de 530 mil linhas
  por mês) antes de fixar. Instâncias de núcleo compartilhado não têm SLA: servem para o P3, não para
  o lançamento público.
- **Conexão:** pelo conector do Cloud SQL integrado ao Cloud Run (criptografado e autorizado pelo
  IAM). IP público sem nenhuma rede autorizada e SSL obrigatório. IP privado (VPC) fica para depois.
- **Usuários:** os do ADR 0006 (`rx_dono`, `rx_api`, `rx_ingestao`), criados uma vez pelo
  administrador, com senhas fortes guardadas só no Secret Manager. O `banco/preparar.py` continua só
  para desenvolvimento e CI; a preparação de produção é um passo manual do roteiro de operação.
- **Backups:** automático diário, com 7 cópias, e recuperação a um ponto no tempo de 7 dias. Backup
  sob demanda antes de cada migração (ADR 0006, seção 8).
- **LGPD:** um e-mail excluído da lista de espera continua nos backups por até 7 dias (ponto já
  registrado no ADR 0006 para a política de privacidade).
- **Manutenção:** janela na madrugada de domingo.

### 5. Cargas agendadas

| Carga | Quando (horário de Brasília) |
|---|---|
| CVM, composição dos fundos (CDA) | Todo dia às 9h (a CVM atualiza de terça a sábado, às 8h) |
| CVM, FCA e cadastros | Toda segunda às 9h |
| PTAX | Dias úteis às 13h30, com nova tentativa às 18h |
| SEC (tickers e N-PORT) | Quando o e-mail do projeto e a liberação do N-PORT estiverem prontos |

- Cada carga é um Cloud Run Job disparado pelo Cloud Scheduler, com o usuário `rx_ingestao`, uma
  nova tentativa automática e tempo limite.
- Uma falha deixa a carga em `com_erro` (ADR 0006, seção 3) e dispara alerta (seção 8). A API segue
  com os dados publicados antes.
- As cargas acessam a internet pela saída padrão do Cloud Run. Nenhuma fonte exige IP fixo.

### 6. Segredos e contas de serviço

- Uma conta de serviço por peça, com o mínimo de permissão:
  - `rx-api`: cliente do Cloud SQL e o segredo do `rx_api`;
  - `rx-cargas`: cliente do Cloud SQL e o segredo do `rx_ingestao`;
  - `rx-migracoes`: cliente do Cloud SQL e o segredo do `rx_dono`;
  - `rx-deploy`: usada pelo GitHub Actions para publicar imagens e fazer o deploy, sem acesso ao banco.
- O GitHub Actions entra no Google Cloud por **Workload Identity Federation**: nenhuma chave de conta
  de serviço (arquivo JSON) existe em lugar nenhum.
- Segredos nunca entram no repositório, na imagem ou nos logs. A troca de senha fica no roteiro de
  operação.

### 7. Deploy

- Um workflow de deploy no GitHub Actions, disparado à mão e protegido pelo ambiente `producao` do
  GitHub, que pede a aprovação do Lucas:
  1. confere que o CI da `main` está verde;
  2. constrói a imagem do backend, marcada com o commit, e publica no Artifact Registry;
  3. faz backup do banco e roda o job `migrar`;
  4. publica a nova revisão da API no Cloud Run;
  5. publica o front no Firebase Hosting.
- **Voltar atrás:** a revisão anterior da API continua no Cloud Run e volta com um comando. As
  migrações só vão para frente; uma migração com erro se corrige com outra (ADR 0006).
- Depois do P3, o deploy pode passar a sair sozinho a cada merge na `main`.

### 8. Logs, retenção e alertas

- Os logs da aplicação já não registram carteira nem dados de entrada (`backend/CLAUDE.md`).
- **Retenção de 180 dias** no bucket de logs. Os registros de acesso do Cloud Run trazem o IP de quem
  acessou, e o Marco Civil da Internet (Lei 12.965/2014, art. 15) obriga o provedor de aplicação a
  guardá-los por 6 meses *(a confirmar com o M1)*.
- **Alertas por e-mail**, para o e-mail do projeto (R-05):
  - carga com erro;
  - fonte sem carga nova além do esperado (ex.: CDA sem publicação há 3 dias);
  - API respondendo com erros 5xx;
  - `/saude` fora do ar (verificação de disponibilidade);
  - orçamento em 50%, 90% e 100%.

### 9. Custo

- Ordem de grandeza no P3: algumas dezenas de dólares por mês, quase tudo no Cloud SQL e na instância
  mínima da API. O valor exato se confere na calculadora do Google Cloud antes de criar os recursos.
- Orçamento com alertas (seção 8) desde o primeiro dia.

### 10. Fases

| Fase | O que entra |
|---|---|
| **Antes do P3** | Projeto, faturamento e orçamento. Cloud SQL, Artifact Registry, Secret Manager e contas de serviço. Dockerfile do backend e workflow de deploy. API no Cloud Run e front no Firebase, com domínio e HTTPS. Jobs da CVM e da PTAX com o Cloud Scheduler. Alertas e roteiro de operação. |
| **Depois do P3** | Ambiente de homologação. IP privado para o banco. Limite por IP na borda (Cloud Armor) ou contador compartilhado (DT-2). Infraestrutura como código (Terraform). Jobs da SEC. Deploy automático a cada merge. |

### A decidir

- O domínio do produto.
- Quem tem acesso de administrador ao projeto (proposta: Lucas e M1, com verificação em duas etapas).
- O valor do orçamento mensal.
- O e-mail que recebe os alertas (o e-mail do projeto, quando existir).

## Consequências

- **ADR 0006:** a versão do PostgreSQL fica confirmada (17) e o backup antes da migração passa a ser
  o passo 3 do deploy.
- **DT-1** fecha com a carga diária da PTAX. **DT-2** continua (contador por instância, com no máximo
  3 instâncias). **DT-4** ganha a opção C (várias instâncias). **DT-10** é medida no Cloud Run e no
  Cloud SQL.
- **Arquivos novos**, em PRs próprios: Dockerfile do backend, workflow de deploy, configuração do
  Firebase e o roteiro de operação (`docs/runbooks/producao.md`).
- **O que só o Lucas pode fazer:** criar o projeto e a conta de faturamento, registrar o domínio e dar
  os acessos. Os comandos ficam no roteiro de operação.

## Alternativas descartadas

- **Outra região (ex.: `us-central1`):** mais barata, mas com os dados fora do Brasil e mais latência
  para o usuário.
- **Kubernetes (GKE):** complexidade sem necessidade para quatro peças pequenas.
- **Máquina virtual (Compute Engine):** atualização, segurança e backup do servidor por nossa conta.
- **Banco numa máquina virtual:** backup, atualização e alta disponibilidade por nossa conta.
- **Front no Cloud Storage com balanceador de carga:** o balanceador tem custo fixo mensal; o Firebase
  entrega o mesmo, com HTTPS e domínio, sem custo fixo.
- **Chave JSON de conta de serviço no GitHub:** um vazamento daria acesso ao projeto; o Workload
  Identity Federation não guarda segredo.
