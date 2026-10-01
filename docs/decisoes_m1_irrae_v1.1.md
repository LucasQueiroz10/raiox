# Decisões do M1 — IrRAE v1.1, divergências do repositório e tarefa T-01

- **Data:** 01/10/2026
- **Autor:** M1 (dono da metodologia, ADR 0004)
- **Destino:** Claude Code do repositório `raiox`, e o Lucas (M2) para as decisões conjuntas
- **Caminho sugerido no repositório:** `docs/decisoes_m1_irrae_v1.1.md`
- **Aprovação do M1:** [x] aprovado em 01/10/2026 (confirmado pelo Lucas)

---

## 0. Como ler este documento (instruções para o agente)

1. Cada item tem um ID: `D-xx` (decisão sobre a revisão do prompt v1.1, na mesma numeração 1–21 da revisão), `X-xx` (decisão extra), `R-xx` (divergência entre o repositório e as decisões) e `T-xx` (tarefa).
2. Leia a coluna **Status** antes de agir:
   - **DECIDIDO:** implemente como está escrito.
   - **CONJUNTA:** precisa da aprovação do Lucas também (ADR 0004). Não implemente antes disso.
   - **PENDENTE M1:** o M1 ainda vai decidir. Não implemente; se bloquear algo, pergunte.
   - **EM ESPERA:** não mexa. As fontes de dados ainda aguardam autorização (ver seção 4).
3. Continuam valendo todas as regras do `CLAUDE.md`: teste primeiro, PRs pequenos, só fontes permitidas ou provisórias na `docs/matriz_de_dados.md`, só dados sintéticos em código e testes, nenhum segredo no diff.
4. Ao terminar um item, cite o ID no título do PR ou do commit (ex.: `fix(irrae): D-01 troca o teste de largura pela variância`).

---

## 1. Decisões sobre a revisão do prompt v1.1 (itens 1 a 21)

### A. Contradições e erros

| ID | Tema | Decisão | Status |
|---|---|---|---|
| D-01 | Teste 5 e nomes da faixa | Ver detalhamento abaixo da tabela. | DECIDIDO |
| D-02 | Ciclo de ETFs | Seguir a regra do produto: recalcular até a diferença ficar abaixo de 0,1% (`CONVERGENCIA_CICLO = 0.001`, como em `app/core/lookthrough.py`) e mandar o resto para "não aberto". **Sem erro.** O teste 4 passa a conferir que o ciclo converge e que o resto vai para "não aberto". | DECIDIDO |
| D-03 | Identificador da entrada | Ver D-08 e R-01/R-02. A entrada do `irrae/` aceita ISIN e valores (D-17). CUSIP fica de fora até o resultado da T-01. | DECIDIDO |
| D-04 | Tamanho do PR | Vários PRs pequenos, nesta ordem: (1) remover o E; (2) calibração vira auditoria; (3) filtro do N; (4) agregação da carteira com o teste 5 novo; (5) relatório e changelog. | DECIDIDO |
| D-05 | Pilar do N | **O N continua no pilar Percepção.** Assim a regra "percepção não cria tema" continua agindo. A pergunta "N passa a Realizado?" está encerrada. | DECIDIDO |
| D-06 | Seções do relatório a atualizar | Aceita a lista completa da revisão: 7.1 (Tabela 5, linha do E), 7.4 (Tabela 7: coluna "Combinado" e a legenda que diz que a calibração "corrige"), 10 (passos 3 e 6 e as limitações 4 e 5) e 11 (estrutura do código e caminhos do zip). | DECIDIDO |

**D-01 em detalhe**

1. Remover a afirmação "largura comonotônica ≥ largura independente". Ela é falsa em geral. Contraexemplo: duas empresas com 50% cada, cada uma com 0% em 96% dos sorteios e 100% em 4%. O P95 comonotônico é 0%; o independente é 50%, porque 1 − 0,96² = 7,84% > 5%.
2. O teste 5 passa a conferir, em toda área (folha e tema), com tolerância só de ponto flutuante (`1e-9`):
   - variância comonotônica ≥ variância independente;
   - média dos 5% maiores sorteios (k = ⌈0,05·S⌉): comonotônica ≥ independente;
   - média dos 5% menores sorteios: comonotônica ≤ independente.

   As três desigualdades valem **exatamente dentro da amostra**, porque as duas versões usam os mesmos sorteios (desigualdade de rearranjo; Marshall, Olkin e Arnold, *Inequalities: Theory of Majorization*, 2011, cap. 6; Dhaene et al., 2002, *Insurance: Mathematics and Economics* 31(1)). A tolerância serve só para casos como o de uma folha com uma única empresa, em que os dois cenários são idênticos e diferem em ~1e-17.
3. Corrigir no código atual:
   - `tests/irrae/test_irrae_agregacao_etf.py`, `test_comonotonico_mais_largo_e_quantis_somam`: remover a checagem de largura e manter a checagem de que os quantis somam.
   - `irrae/agregacao.py`, docstring: trocar "casos-limite" por "cenários de referência" e apagar "A verdade fica entre os dois".
4. Nomes que aparecem em saídas e relatórios: "faixa estimada (cenário independente)" e "faixa estimada (cenário de erros alinhados)". Nunca "IC", "IC90", "intervalo de confiança" nem "limite". O mesmo vale para a faixa por ação.

### B. Lacunas

| ID | Tema | Decisão | Status |
|---|---|---|---|
| D-07 | Universo de empresas | Na v1.1, só empresas que entregam **10-K**. Ações da B3 e empresas que entregam 20-F (ex.: TSMC, ASML) vão para "não coberto". O 20-F tem outra numeração (risco no Item 3.D, negócio no Item 4, análise no Item 5) e fica para a v1.2. | DECIDIDO |
| D-08 | Consolidar classes da mesma empresa | No N-PORT, consolidar pelo **LEI** do emissor (GOOGL e GOOG têm o mesmo LEI). Para as empresas do escopo (50 a 100), manter uma tabela CIK ↔ LEI curada à mão, montada só com dados já permitidos (campo `lei` do N-PORT e filings da SEC). **Não usar a API do GLEIF** (EM ESPERA, seção 4). | DECIDIDO |
| D-09 | MD&A no N | Usar só a subseção "Results of Operations" do Item 7, localizada pelo título, mais o filtro de frases prospectivas. A regra "frases sobre operações do período" sai do prompt. | DECIDIDO |
| D-10 | "Descrições de segmentos" no N | **Não entram no N.** A nota de segmentos (Item 8) é a mesma evidência que o componente A já usa; contá-la duas vezes subestima a incerteza. O N lê só o Item 1 e a subseção da D-09. | DECIDIDO |
| D-11 | Amostra para revisão manual | Cerca de 200 frases, estratificadas por folha rotulada (incluindo "nenhuma folha") e por empresa. A entrega é: arquivo CSV com frase, empresa, item, rótulo automático e coluna vazia para o rótulo manual, mais um script que calcula a precisão depois que o M1 rotular. | DECIDIDO |
| D-12 | Alarmes da calibração | Corrigir os alarmes falsos com Bonferroni por empresa: z > Φ⁻¹(1 − 0,10 / (2m)), em que m é o número de folhas testadas na empresa. Com m = 6, o corte é z ≈ 2,39 (antes, 1,645, o que dava ~47% de chance de pelo menos um alarme falso por empresa). Referência: Dunn (1961), *JASA* 56(293). | DECIDIDO |
| D-13 | Posições vendidas dentro do ETF | Seguir o produto: vendidos num balde próprio, com sinal negativo e a nota `raiox.nota_posicoes_vendidas`. O "não coberto" nunca fica negativo. Se as compradas passarem de 100% (alavancagem), emitir aviso e não normalizar. | DECIDIDO |
| D-14 | Teste 3 (ETF dentro de carteira) | Calcular os **pesos efetivos antes** e agregar uma vez só. Motivo: se a mesma empresa está na carteira direto e dentro do ETF, agregar o ETF primeiro a embaralha separadamente de si mesma no cenário independente, e a faixa sai estreita demais. | DECIDIDO |
| D-15 | Semente | A calibração usa um gerador de números aleatórios próprio, separado do gerador dos sorteios do IrRAE, para não mudar os sorteios seguintes e não quebrar os testes 1 e 2. | DECIDIDO |
| D-16 | Código do E | **Apagar** (sem flag; o histórico do Git guarda o código). Remover também `E_enquadramento` e a correlação `N_narrativa|E_enquadramento` do `irrae/config/componentes.json`, o E do gerador sintético (incluindo o viés de hype ×1,8), `posicoes_sem_etf` e `de_etfs`. O teste 7 sai. Remover os dois testes do E está aprovado pelo M1. Fechar a DT-7 no mesmo PR. | DECIDIDO |
| D-17 | Entrada do `irrae/` | Aceita ISIN e valores, para servir ao lote do MVP. No protótipo 1, a carteira do `irrae/` é só hipotética (análise e testes). Testes usam apenas ISINs sintéticos. | DECIDIDO |

### C. Forma do prompt

| ID | Tema | Decisão | Status |
|---|---|---|---|
| D-18 | Relatório técnico fora do repositório | Trazer o relatório técnico v1 para o repositório (sugestão: `docs/irrae/relatorio_tecnico_v1.*`). Pela ADR 0004, a única fonte da verdade é o repositório. O M1 envia o arquivo. | PENDENTE M1 (envio do arquivo) |
| D-19 | Caminhos e amarras no prompt | O prompt revisado cita `backend/irrae/`, `backend/ingest/nport.py`, a ADR 0004, a DT-7, a matriz de dados, o `textos_telas.md`, a regra de teste primeiro e a aprovação para remover os testes do E (D-16). | DECIDIDO |
| D-20 | "Confirmar antes de fechar" | Passa a ser "confirmar antes de implementar a seção 4 (N)". O único ponto que continua em aberto é a **lista final de marcadores prospectivos** (expect, anticipate, plan, intend, believe, may, will, could, aim, seek, "forward-looking"), que o M1 ainda aprova. | PENDENTE M1 (lista de marcadores) |
| D-21 | Registro da aprovação | A aprovação do M1 fica registrada na descrição de cada PR da v1.1 e numa atualização da ADR 0004 (seção "Pontos em aberto"). | DECIDIDO |

### D. Decisões extras

| ID | Tema | Decisão | Status |
|---|---|---|---|
| X-01 | Regras do `frontend/CLAUDE.md` | Na `main`, as regras "A carteira nunca é enviada a terceiros" e "Sem analytics" existem. Se sumiram em algum branch de trabalho, restaurar com o texto exato da `main`. | DECIDIDO |
| X-02 | Faixa da carteira na tela do produto | Pela ADR 0004, o lote grava por empresa só média, P5 e P95, sem os sorteios. Com isso, a API só consegue calcular o cenário de erros alinhados (soma dos quantis ponderados). Recomendação do M1: **(a)** mostrar só essa faixa, com o nome "faixa estimada, supondo que os erros das empresas andam juntos", sem chamá-la de "conservadora"; o cenário independente fica só nos relatórios do lote. A alternativa **(b)** (gravar os sorteios e levar numpy para a API) muda arquitetura e dependências. | CONJUNTA (Lucas) |
| X-03 | Reaproveitar o look-through do produto no `irrae/` | Para não haver duas implementações de ciclo (D-02), avaliar se o `irrae/` pode reutilizar `app/core/lookthrough.py` (a regra é que `app/` não importa `irrae/`; o contrário não está proibido). | CONJUNTA (Lucas) |

---

## 2. Divergências entre o repositório e as decisões

| ID | Ponto | Onde no repositório | O que fazer | Status |
|---|---|---|---|---|
| R-01 | CUSIP como chave | `irrae/agregacao.py`, `pesos_da_carteira(campo="cusip")` | Depois da T-01: se ela der ≥ 95%, trocar o padrão para LEI, com ticker e nome como alternativas, e deixar o CUSIP como opção desligável. Se der bem menos, manter como está até a resposta da CGS ao formulário UOSS. **Não mudar antes da T-01.** | Aguarda T-01 |
| R-02 | "A chave de empresa é o ISIN" | `CLAUDE.md` da raiz e ADR 0003 | Funciona para ISINs brasileiros. ISINs americanos são CGS ISINs (mesma licença do CUSIP). Proposta: `empresa_id` interno, com uma tabela de identificadores (ticker, CIK, LEI, ISIN BR; CUSIP e ISIN US em campo opcional). Decisão de arquitetura. | CONJUNTA (Lucas) |
| R-03 | Matriz de dados defasada (AIPD, FSN, Patent Assignment, GLEIF, `company_tickers`, PatentsView no ODP) | `docs/matriz_de_dados.md` | **Não mexer.** As fontes ainda aguardam autorização do M1. Ver seção 4. | EM ESPERA |
| R-04 | Duas fontes da verdade (planilha do M1 × matriz) | Planilha `Fontes_de_dados_IrRAE.xlsx` e `docs/matriz_de_dados.md` | O M1 passa os status validados para a matriz quando terminar as autorizações. O agente não altera a matriz por conta própria. | EM ESPERA |
| R-05 | E-mail do User-Agent | Matriz, ponto de atenção 3 | Precisa ser um e-mail do projeto no domínio `sagitalapp.com.br`, real e monitorado (sugestão: `dados@sagitalapp.com.br`). O M1 define. **Bloqueia a T-01.** | PENDENTE M1 |
| R-06 | GLEIF | Fora da matriz | Não usar. Quando for autorizado, as condições já levantadas são: licença CC0, mas proibido sugerir vínculo com o GLEIF ou usar o logo, sob multa contratual de CHF 100.000 e foro em Basileia. | EM ESPERA |
| R-07 | ADR 0004, ponto em aberto 3 ("faixa pelo limite comonotônico") | `docs/adr/0004-modelo-irrae.md` | Reescrever: são dois cenários de referência, nenhum é limite da faixa; o nome é "faixa estimada". Ligar com X-02. | DECIDIDO |
| R-08 | DT-3 × v1.1 | O produto separa classes de ações pelo ISIN (DT-3); a v1.1 consolida pela empresa | Alinhar: no lado do N-PORT, consolidar pelo LEI (D-08); no lado da B3, pelo emissor no Formulário Cadastral da CVM (já previsto na DT-3). **Prazo da DT-3: portão P3, 23/10.** | DECIDIDO |
| R-09 | Nome do produto | O README diz "Projeto RX"; o domínio é Sagital | Decisão dos sócios. **Não alterar** README, textos nem identificadores até a decisão. | PENDENTE M1 |

---

## 3. Tarefa T-01: medir se o CUSIP é dispensável (N-PORT do IVV)

**Objetivo:** decidir se dá para trocar o CUSIP e o ISIN americano pelo LEI como identificador das posições do N-PORT (R-01). O resultado decide se esperamos a resposta da CGS ao formulário UOSS antes de usar CUSIP.

**Pré-requisito:** o e-mail do User-Agent definido pelo M1 (R-05).

**Fonte:** SEC, Form N-PORT (fonte 6 da matriz, status provisória: só desenvolvimento e testes). Regras de acesso: User-Agent `Sagital <e-mail definido em R-05>`, no máximo 10 requisições por segundo, leitura do XML só por `ingest/xml_seguro.ler_xml`. É a primeira execução real dos leitores de `ingest/`.

**Passos:**
1. Localizar no EDGAR o N-PORT-P mais recente do **iShares Core S&P 500 ETF (IVV)** e baixar o XML.
2. Ler com `ingest/nport.parse_nport`. Hoje ele extrai `name`, `lei`, `cusip` e `isin`, mas **não** o ticker: estender para ler `identifiers/ticker` (com teste e fixture sintética antes, conforme o `CLAUDE.md`).
3. Filtrar as posições compradas em ações: `assetCat == "EC"` e `payoffProfile == "Long"`. Informar à parte o peso do que ficou de fora (caixa, derivativos, outros).
4. Para cada posição, classificar pela primeira regra que se aplicar:
   - **LEI válido:** 20 caracteres e dígito verificador ISO 17442 (mod 97) correto;
   - **só ticker:** sem LEI válido, mas com ticker;
   - **só nome:** sem LEI nem ticker;
   - **só CUSIP/ISIN:** sem LEI, sem ticker e sem nome utilizável.
5. Somar o `pctVal` de cada grupo.

**Saída (só números agregados, em Markdown, no PR):**

| Grupo | % do peso das ações | Nº de posições |
|---|---|---|
| LEI válido | | |
| Só ticker | | |
| Só nome | | |
| Só CUSIP/ISIN | | |
| **LEI + ticker** | | |

E também: o número de LEIs repetidos entre posições diferentes (indica classes da mesma empresa, ex.: GOOGL/GOOG) e a data de referência do N-PORT (`repPdDate`).

**Regra de decisão:**
- **LEI + ticker ≥ ~95% do peso:** o CUSIP é dispensável. Abrir o PR de R-01.
- **Bem abaixo de 95%:** manter o CUSIP fora do produto até a resposta da CGS ao UOSS. Informar ao M1 quanto do peso fica dependendo de "só nome".

**Cuidados:**
- **Não** commitar o XML baixado nem nenhuma lista de CUSIPs ou ISINs americanos. Guardar o arquivo fora do repositório ou numa pasta no `.gitignore`. O resultado é só a tabela agregada.
- O script é de análise, não do produto: fica fora de `app/` (sugestão: `backend/ingest/` com a função testada, e a chamada pontual fora do CI).

---

## 4. EM ESPERA: não implementar

Aguardando a autorização de cada fonte pelo M1. **Não desenvolver leitores, APIs, ingestões nem mudanças na matriz** para:

- USPTO AI Patent Dataset (AIPD)
- SEC Financial Statement and Notes Data Sets (FSN)
- USPTO Patent Assignment (dataset da OCE e XML diário/anual)
- USPTO PatentsView / Open Data Portal
- GLEIF (LEI e Level 2), inclusive a API
- SEC `company_tickers.json`

O código que já existe no repositório para essas fontes (ex.: `ingest/patentes.py`) continua como está e só roda com fixtures.

---

## 5. Ordem de execução sugerida

1. PR de documentação: R-07 (ADR 0004, ponto 3) e X-01 (se as regras do frontend tiverem sumido em algum branch).
2. T-01, assim que o M1 definir o e-mail (R-05).
3. PRs da v1.1, na ordem de D-04. A seção 4 do N só depois da lista de marcadores (D-20).
4. R-08 / DT-3 até o portão P3 (23/10).
5. Depois do resultado da T-01: R-01. Depois da decisão conjunta: R-02, X-02 e X-03.

## 6. O que o agente não decide

- Metodologia (fontes, κ, limiares, regras, taxonomia, mapeamentos, forma de apresentar): M1.
- Arquitetura, custo, dependências pesadas e o que aparece na tela: conjunta (M1 + Lucas).
- Nome do produto, e-mail do projeto e autorização de fontes: M1.

Na dúvida, pare e pergunte, citando o ID do item.
