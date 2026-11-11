# ADR 0009: Produto arquivado e vitrine das três carteiras

- **Status:** aceito em 10/11/2026 (arquivamento do produto e rumo da vitrine). Os pontos da seção 5
  ainda esperam decisão.
- **Data:** 2026-11-10.
- **Decisor:** Lucas (Membro 2). A vitrine é um projeto conjunto do Lucas e do M1; o que muda a
  metodologia do IrRAE continua com o M1 (ADR 0004).
- **Relacionados:** ADR 0004 (IrRAE), 0005 (identificação), 0006 (banco e lista de espera, seção 9),
  0007 (hospedagem), 0008 (carga da CVM); especificação da vitrine em `docs/vitrine/especificacao.md`;
  DT-2, DT-4, DT-11 e DT-17.

## Contexto

Até 15/10/2026 (PR #82), o trabalho ia rumo ao P3 (teste fechado com usuários, 23/10/2026) e ao
protótipo 1 (06/11/2026): a API `POST /api/raiox`, as cargas da CVM e da PTAX, o banco e a imagem
Docker estavam prontos; faltavam o deploy, as telas e a importação de CSV.

Nada chegou a ser publicado (confirmado pelo Lucas em 10/11/2026): não houve deploy, a lista de
espera nunca recolheu e-mails e nenhuma migração cria a tabela dela. Não há dado pessoal a apagar.

Em 10/11/2026 o Lucas decidiu arquivar a Sagital como produto, com a possibilidade de retomar no
futuro, e seguir com uma vitrine: um site que mostra o raio-x e o IrRAE em três carteiras públicas,
sem que o visitante informe carteira nenhuma.

## Decisões

### 1. O produto fica arquivado, não apagado

- **Marco:** a tag anotada `produto-arquivado-2026-11` aponta para o commit `9baaa5c` (merge do
  PR #82), o último estado do produto. Retomar começa por ela (seção 4).
- **O código continua na `main` e no CI:** API, motor, banco, cargas, imagem Docker e testes. Nada é
  apagado. A vitrine reaproveita o `app/core/lookthrough.py` (X-03), o `irrae/` e as cargas da CVM; e
  o CI mantém o código do produto funcionando até a retomada.
- **Ficam parados:** o deploy no Google Cloud (ADR 0007), as cargas agendadas, a lista de espera
  (ADR 0006, seção 9), a importação de CSV da B3 e da Avenue e as telas de cadastro.
- **Os ADRs 0001 a 0008 continuam valendo** para o produto. Este ADR não revoga nenhum deles; só
  suspende o que depende de a API estar publicada.
- **Dívidas suspensas:** DT-2, DT-4, DT-11 e DT-17 só existem com a API no ar. Ficam no
  `docs/divida_tecnica.md`, marcadas como suspensas, para a retomada.
- **A marca continua:** a vitrine é da Sagital.

### 2. A vitrine

Site estático, sem fins comerciais, de autoria do Lucas e do M1. O visitante escolhe uma de três
carteiras fixas e vê o raio-x dela, com a exposição à Cadeia de IA pelo IrRAE. A especificação
completa, com as correções da conferência de 10/11/2026, está em `docs/vitrine/especificacao.md`.

| Carteira | Composição | Como chega às empresas |
|---|---|---|
| `big-techs` | NVIDIA, Amazon, Apple e Microsoft, 25% cada | Ações diretas |
| `sp500` | 100% no IVV | Carteira do ETF no N-PORT da SEC (fonte 6, liberada pelo M1 em 12/10/2026) |
| `ibovespa` | 100% no BOVA11 | Carteira do ETF no CDA da CVM (fonte 1) |

- **Sem entrada de dados do visitante:** nada de carteira, ticker, arquivo, conta ou e-mail.
- **Sem servidor de cálculo:** os resultados são calculados antes, em lote, e publicados como
  arquivos JSON (snapshots), um por carteira. O navegador não chama a API da Sagital nem serviços
  externos, e o site não tem analytics.
- **Enquanto não houver cálculo com dados reais,** o site usa snapshots sintéticos e mostra a faixa
  "Dados ilustrativos". Nunca números "realistas" inventados para empresas reais.
- **Contrato do snapshot:** um modelo Pydantic no backend define o formato e exporta um JSON Schema;
  o tipo TypeScript do front é gerado desse esquema, como os tipos da API, e nunca é escrito à mão.
  O front valida o arquivo ao carregar e mostra um erro claro se ele não bater.
- **Script de snapshot no backend** (`backend/scripts/`), usando o `app/core/lookthrough.py` e o
  `irrae/`, com testes em dados sintéticos. Ele confere que temas + fora do tema + não coberto = 100%
  e falha se não fechar.
- **Identificação:** como no ADR 0005. Nenhum CUSIP, SEDOL ou ISIN fora da lista permitida, nem no
  snapshot.

### 3. Regras de dados

- As três carteiras são públicas e nada é recebido do visitante: a vitrine não trata dado pessoal.
- Continua valendo "só dados sintéticos em código, testes, logs e conversa" até a decisão V-01
  (seção 5).
- A faixa da carteira e qualquer texto sobre ela seguem a D-01 de `docs/decisoes_m1_irrae_v1.1.md`
  até o M1 decidir o ponto da seção 5.

## 4. Como retomar o produto

1. Escrever um ADR que revogue este, recolocar a seção "Fase atual" do `CLAUDE.md` da raiz e decidir
   se a vitrine continua junto.
2. Partir da `main` (o código do produto está nela, testado). A tag `produto-arquivado-2026-11` mostra
   o estado exato em que o produto parou, para comparar.
3. Atualizar as dependências e a imagem (o `Dockerfile` fixa a base pelo digest) e rodar os testes e
   `backend/scripts/testar_imagem.sh`.
4. Retomar as pendências na ordem em que estavam em 15/10/2026:
   1. **Infraestrutura:** projeto no Google Cloud com faturamento, DNS do sagitalapp.com.br e ambiente
      `producao` no GitHub, com aprovação do Lucas.
   2. **Workflow de deploy** (ADR 0007, seção 7): manual, com as variáveis `RX_PROXIES_CONFIAVEIS`
      (obrigatória em produção) e `RX_SEGREDO_AQUECIMENTO`, e as cargas no Cloud Scheduler (CDA de
      terça a sábado às 9h, cadastro às segundas às 9h, PTAX nos dias úteis às 13h30 e às 18h,
      aquecimento às 9h45).
   3. **DT-17:** medir a posição do IP no primeiro deploy (o `firebase.json` precisa encaminhar só
      `/interno/ip-do-cliente`) e depois remover a medição.
   4. **PR 2.1 do ADR 0008:** categoria "confidencial", crédito sem emissor separado e os avisos de
      composição com mais de 90 dias e de fundo sem composição utilizável (os textos já estão em
      `docs/textos_telas.md`). Mexe em motor, API e banco: plano antes.
   5. **Importação de CSV da B3 e da Avenue:** conseguir arquivos de exemplo e conferir se o da B3 traz
      ISIN, CNPJ e renda fixa.
   6. **Telas do produto** (cadastro e raio-x) e HTTPS.
   7. **Lista de espera:** só com o bloco da seção 9 do ADR 0006 (tabela, papel `rx_admin_lista` e
      funções de acesso) e com o aviso de privacidade aprovado pelo M1 antes de recolher qualquer
      e-mail.
5. **Cobertura de ativos** (medida em 14/10/2026), do maior risco para o menor:
   - ações e ETFs americanos (Avenue): faltam a tabela de empresas da SEC (fonte 7) e o N-PORT;
   - BDRs, sem companhia no FCA;
   - ETFs da B3: só 27 tickers ligados ao CNPJ;
   - renda fixa, que a API ainda não aceita.

   O N-PORT e a tabela da SEC feitos para a vitrine fecham boa parte do primeiro item.
6. **Esperando o M1:**
   - DT-16;
   - os tipos de linha do CDA que ele não decidiu;
   - a revisão dos textos de tela, todos em rascunho;
   - se a frase do aviso do BCB é oficial;
   - a P-1 (agregação da carteira no IrRAE, PR 4 da v1.1).
7. **Antes do MVP:** contas e carteiras gravadas pedem um ADR próprio (LGPD: consentimento,
   criptografia e retenção).

## 5. Pendentes

| # | Decisão | Proposta | Quem decide |
|---|---|---|---|
| V-01 | Snapshots com dados reais no repositório, contra a regra de só dados sintéticos | Exceção no `CLAUDE.md` só para `frontend/public/snapshots/` (dados públicos, sem dado pessoal) | Lucas |
| V-03 | Licença do snapshot do `ibovespa`: o JSON baixado pelo navegador é uma base derivada da CVM, e a ODbL pede a mesma licença | Declarar ODbL no próprio JSON e na página `/fontes` | Lucas, de preferência com advogado (matriz, ponto de atenção 1) |
| V-04 | Corte de cobertura do IrRAE no `sp500` e no `ibovespa` | Maiores posições até a maior cobertura possível; o resto "não coberto" ou "só prior", sempre com a cobertura na tela | M1 |
| V-06 | Repositório público ou privado | Repositório privado; publicar só o site gerado | Lucas |
| V-07 | Hospedagem e domínio | Hospedagem estática (o Firebase Hosting já está no ADR 0007) | Lucas |
| V-09 | Faixa da carteira: a especificação mostra só o cenário comonotônico, e a D-01 apresenta os dois cenários de referência | Levar ao M1; até lá, seguir a D-01 | M1 |

Já decididos em 10/11/2026: código do produto mantido (V-05), N-PORT liberado desde 12/10/2026
(V-02), autoria do Lucas e do M1 (V-08) e a marca Sagital.

## Consequências

- **Positivas:** o produto pode voltar do ponto em que parou, com o roteiro acima. A vitrine não trata
  dado pessoal, não precisa de servidor de cálculo e reaproveita o motor e o modelo.
- **Negativas:** o CI segue testando um código que não está em uso, e o Dependabot segue propondo
  atualizações para ele. Os dados reais da vitrine dependem de ingestões que ainda não existem
  (tabela da SEC, N-PORT em escala e as fontes do IrRAE por empresa); até lá, ela mostra só dados
  ilustrativos.
