# ADR 0007: Hospedagem no Google Cloud

- **Status:** proposto
- **Data:** 2026-10-12. Revisado no mesmo dia: rotas sob `/api`, endereço `run.app`, releitura dos
  dados sem trava, provedor de identidade restrito ao repositório, domínio e cookies; à noite, o
  horário da carga da CDA (ADR 0008).
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
- **Domínio:** `sagitalapp.com.br`, já registrado, apontado para o Firebase Hosting.

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

**Rotas sob `/api`:** o Firebase repassa o caminho inteiro (um pedido a `/api/raiox` chega à API
como `/api/raiox`). Por isso as rotas da API ficam sob `/api` em todos os ambientes, para o
desenvolvimento e a produção se comportarem igual: `/api/raiox`, `/api/saude` e, depois,
`/api/fontes` e `/api/lista-espera`. Fora do `/api` fica só o endpoint interno de aquecimento
(seção 3), que o Firebase não encaminha.

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
  nunca o primeiro. A posição exata é conferida no primeiro deploy, com pedidos nossos: um pelo
  domínio e outro direto ao endereço `run.app` (abaixo), registrando a estrutura do cabeçalho nos
  dois casos (só as posições, nunca os IPs). Nunca `--forwarded-allow-ips="*"` sem esse tratamento
  (`backend/CLAUDE.md`). A medição usa o endpoint interno temporário `GET /interno/ip-do-cliente`
  (DT-17), com o segredo do aquecimento. Depois de registrar as posições aqui e acertar
  `RX_PROXIES_CONFIAVEIS`, o endpoint sai num PR próprio e a DT-17 fecha (roteiro de operação,
  seção 3, passo 5).
- **Tempo por requisição:** o encaminhamento do Firebase tem limite de 60 s; o pior caso da análise
  fica em uns 2 s (DT-4).
- **Cobrança por pedido** (o padrão do Cloud Run): a CPU só existe enquanto há pedido em andamento.
  Por isso nada roda em segundo plano na API: todo trabalho acontece dentro de um pedido.

**Releitura dos dados sem travar as análises** (DT-10):

- A primeira leitura da foto dos dados acontece na partida do servidor, antes de ele aceitar
  pedidos. Se o banco não responder, o servidor sobe mesmo assim, e as análises recebem 503
  `dados_indisponiveis` até uma leitura dar certo. Sem foto, só um pedido por vez tenta ler; os
  outros recebem 503 na hora.
- Quando um pedido percebe uma carga nova (conferência no máximo a cada minuto), só ele monta a
  foto nova, fora da trava, com a marcação de releitura em andamento. Os demais seguem com a foto
  anterior, sem esperar. A foto nova entra de uma vez só, quando fica pronta. Durante a releitura há
  duas fotos na memória.
- Depois de uma falha (banco fora do ar) com uma foto para servir, a próxima conferência espera
  5 minutos, para não fazer um usuário por minuto esperar o tempo limite de conexão. Sem nenhuma
  foto, a API já responde 503 a tudo, então tenta de novo no intervalo normal (1 minuto) para voltar
  logo que o banco responder.
- **Aquecimento:** o Cloud Scheduler chama o endpoint interno `POST /interno/aquecer` depois da
  carga da CDA (seção 5), para nenhum usuário pagar a releitura. O endpoint monta a foto
  dentro do próprio pedido e só depois responde (não há CPU fora dos pedidos); não devolve dados;
  e fica fora do `/api`, então o Firebase não o encaminha. Como o endereço `run.app` é público
  (abaixo), ele exige um segredo num cabeçalho (Secret Manager, enviado pelo Cloud Scheduler) e
  responde 404 sem ele. Sem carga nova, só confere a versão e não relê nada. O aquecimento chega a
  uma instância só; com mais de uma no ar, as outras releem no próximo pedido que receberem.

**Endereço `run.app`: risco aceito no P3** (DT-11):

- Todo serviço do Cloud Run tem um endereço público próprio (`...run.app`), e quem o chama direto
  não passa pelo Firebase. Não dá para desligá-lo: o Firebase Hosting usa esse endereço para
  encaminhar os pedidos e está na lista de serviços que param de funcionar sem ele (documentação do
  Cloud Run, conferida em 12/10/2026). Restringir a entrada ao balanceador de carga também bloquearia
  o Firebase.
- A API também não consegue reconhecer com segurança um pedido que não veio pelo Firebase: quem chama
  o `run.app` pode forjar qualquer cabeçalho, e o Firebase não acrescenta um segredo ao pedido que
  encaminha.
- Consequência: quem chamar o `run.app` direto consegue driblar o limite por IP. Continuam valendo as
  4 análises por instância e o máximo de 3 instâncias, que seguram o custo, mas não a
  disponibilidade.
- **Aceito para o P3** (teste fechado, com poucos usuários). **Condição para o lançamento público:**
  migrar para um balanceador de carga do Google na frente de tudo (`/api` para o Cloud Run e o resto
  para um bucket com rede de entrega), com a entrada restrita ao balanceador, o `run.app` desligado e
  o limite por IP na borda (Cloud Armor), o que também resolve a DT-2.

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
| CVM, composição dos fundos (CDA) | De terça a sábado às 9h (a CVM atualiza nesses dias, às 8h; ADR 0008, seção 5) |
| CVM, FCA e cadastros | Toda segunda às 9h |
| PTAX | Dias úteis às 13h30, com nova tentativa às 18h |
| Aquecimento da API (`POST /interno/aquecer`, seção 3) | De terça a sábado às 9h45, depois da carga da CDA; ajustar ao tempo medido da carga |
| SEC (tickers e N-PORT) | Depois da carga da CVM; o e-mail do projeto e o N-PORT foram liberados pelo M1 em 12/10/2026 |

- Cada carga é um Cloud Run Job disparado pelo Cloud Scheduler, com o usuário `rx_ingestao`, uma
  nova tentativa automática e tempo limite.
- **Memória dos jobs: 1 GiB.** Medido em 14/10/2026 no banco local, baixando do portal da CVM, com
  `python -m medicoes.pico_da_carga` (pico do processo, no Windows): a carga do cadastro (FCA de 3
  anos, informe de FII de 2 anos e 3 meses do CDA, todos juntos na memória) chegou a 388 MB em 32 s;
  a da CDA, com 3 meses, a 249 MB em 36 s. Medir de novo no primeiro deploy, no Linux do Cloud Run.
  Se o cadastro passar de 1 GiB, ele passa a ler um mês do CDA por vez, soltando o anterior.
- Uma falha deixa a carga em `com_erro` (ADR 0006, seção 3) e dispara alerta (seção 8). A API segue
  com os dados publicados antes. Se nem o registro da falha der certo (banco fora do ar), o job
  termina com erro, sem traceback, e quem avisa é o alerta de fonte sem carga nova.
- As cargas acessam a internet pela saída padrão do Cloud Run. Nenhuma fonte exige IP fixo.
- Se a carga da CDA atrasar, o aquecimento não acha carga nova e não faz nada; o primeiro pedido
  depois da publicação relê (seção 3).

### 6. Segredos e contas de serviço

- Uma conta de serviço por peça, com o mínimo de permissão:
  - `rx-api`: cliente do Cloud SQL e o segredo do `rx_api`;
  - `rx-cargas`: cliente do Cloud SQL e o segredo do `rx_ingestao`;
  - `rx-migracoes`: cliente do Cloud SQL e o segredo do `rx_dono`;
  - `rx-deploy`: usada pelo GitHub Actions para publicar imagens e fazer o deploy, sem acesso ao banco.
- O GitHub Actions entra no Google Cloud por **Workload Identity Federation**: nenhuma chave de conta
  de serviço (arquivo JSON) existe em lugar nenhum.
- O provedor de identidade aceita só o repositório `LucasQueiroz10/raiox`, conferido pelo nome e pelo
  número interno do repositório e do dono no GitHub, que não mudam se o repositório for renomeado e
  não são reaproveitados. A conta `rx-deploy` aceita só os jobs do ambiente `producao` do GitHub.
  Comandos no roteiro de operação (`docs/runbooks/producao.md`).
- O segredo do aquecimento (seção 3) fica no Secret Manager: a API o lê, e o deploy o grava no
  cabeçalho do job do Cloud Scheduler. Na API ele é opcional (`RX_SEGREDO_AQUECIMENTO`, com pelo
  menos 32 caracteres): sem ele, o aquecimento responde 404 e o job falha, o que dispara o alerta
  da seção 8.
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
  - falha no job de aquecimento (avisa também se faltar o segredo na API);
  - fonte sem carga nova além do esperado (ex.: CDA sem publicação há 3 dias);
  - API respondendo com erros 5xx;
  - `https://sagitalapp.com.br/api/saude` fora do ar (verificação de disponibilidade pelo domínio,
    passando pelo Firebase: testa o caminho inteiro);
  - orçamento em 50%, 90% e 100%.

### 9. Custo

- Ordem de grandeza no P3: algumas dezenas de dólares por mês, quase tudo no Cloud SQL e na instância
  mínima da API. O valor exato se confere na calculadora do Google Cloud antes de criar os recursos.
- A API usa a cobrança por pedido (seção 3): parada, a instância mínima é cobrada a uma taxa reduzida,
  e não pela CPU cheia o tempo todo.
- O balanceador de carga com Cloud Armor, condição para o lançamento público (seção 3), traz um custo
  fixo mensal a mais.
- Orçamento com alertas (seção 8) desde o primeiro dia.

### 10. Fases

| Fase | O que entra |
|---|---|
| **Antes do P3** | Projeto, faturamento e orçamento. Cloud SQL, Artifact Registry, Secret Manager e contas de serviço. Dockerfile do backend e workflow de deploy. API no Cloud Run e front no Firebase, com domínio e HTTPS. Jobs da CVM e da PTAX com o Cloud Scheduler. Alertas e roteiro de operação. |
| **Antes do lançamento público** | Balanceador de carga do Google na frente de tudo, com a entrada restrita a ele, o `run.app` desligado e o limite por IP na borda (Cloud Armor). Fecha a DT-2 e a DT-11. |
| **Depois do P3** | Ambiente de homologação. IP privado para o banco. Infraestrutura como código (Terraform). Jobs da SEC. Deploy automático a cada merge. |

### A decidir

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
- **O que só o Lucas pode fazer:** criar o projeto e a conta de faturamento, apontar o DNS do
  `sagitalapp.com.br` para o Firebase Hosting (sem mexer nos registros de e-mail) e dar os acessos.
  Os comandos ficam no roteiro de operação.
- **Fase com contas:** o Firebase Hosting descarta os cookies que não se chamam `__session` antes de
  encaminhar o pedido ao Cloud Run. O cookie de sessão terá de ter esse nome (ADR 0006, "Evolução
  prevista").
- **DT-11:** o endereço `run.app` contorna o limite por IP até o balanceador de carga (seção 3).

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
