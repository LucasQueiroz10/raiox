# Decisões do M1 — IrRAE v1.1, divergências do repositório e tarefa T-01

- **Data:** 01/10/2026 (versão 4)
- **Autor:** M1 (dono da metodologia, ADR 0004)
- **Destino:** Claude Code do repositório `raiox`, e o Lucas (M2) para as decisões conjuntas
- **Caminho sugerido no repositório:** `docs/decisoes_m1_irrae_v1.1.md`
- **Aprovação do M1:** [x] aprovado em 01/10/2026 (versão 4 confirmada pelo Lucas)
- **Atualização de 11/10/2026:** o M1 liberou as fontes da seção 4 pela planilha de fontes
  (`docs/irrae/fontes_de_dados.md`), que ele preencheu e confirmou valer como autorização. R-03 e R-06
  resolvidos; as condições de cada fonte estão na ficha dela e em `docs/matriz_de_dados.md`.

---

## 0. Como ler este documento (instruções para o agente)

1. Cada item tem um ID: `D-xx` (decisão sobre a revisão do prompt v1.1, na mesma numeração 1–21 da revisão), `X-xx` (decisão extra), `R-xx` (divergência entre o repositório e as decisões) e `T-xx` (tarefa).
2. Leia a coluna **Status** antes de agir:
   - **DECIDIDO:** implemente como está escrito.
   - **CONJUNTA:** precisa da aprovação do Lucas também (ADR 0004). Não implemente antes disso.
   - **PENDENTE M1:** o M1 ainda vai decidir. Não implemente; se bloquear algo, pergunte.
   - **EM EXECUÇÃO / EM ANDAMENTO:** já está sendo resolvido fora do repositório. Não implemente; aguarde.
   - **FEITO:** já está no repositório. Nada a fazer.
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
| D-06 | Seções do relatório a atualizar | Lista conferida no PDF do relatório (ver detalhamento abaixo da tabela). Observação: o relatório não tem seção 11; a estrutura do código é o **Apêndice A**. | DECIDIDO |

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

**D-06 em detalhe (conferido no PDF `Relatorio_IrRAE_passo_a_passo.pdf`, versão de 26/09/2026)**

| Onde | O que mudar |
|---|---|
| §1 Resumo e linha do tempo | Tirar o E ("Especulação virou Enquadramento"); trocar "IC" por "faixa estimada"; passo 7 da linha do tempo sem "limites de dependência". |
| Figura 1 | "Calibração por retornos" vira auditoria; "(média e IC)" vira "(média e faixa estimada)". |
| §3.3 e §3.5 | Remover o E; pilar Percepção = só N (D-05). |
| §5.2 | Remover o parágrafo "Enquadramento (ETFs)". |
| §5.10 | A eq. 19 sai do cálculo; a calibração vira diagnóstico, com o corte de Bonferroni (D-12). |
| §5.13 | Trocar "os dois limites" por "dois cenários de referência"; apagar "Dá o intervalo mais estreito" e "Dá o intervalo mais largo" (falso, ver D-01). Manter a frase da ordem convexa e da maior variância [43], que está correta. Apagar o parágrafo "Circularidade". |
| §6.1 | N-PORT só para abrir os ETFs da carteira. |
| §7.1 | Tabela 3 e Figura 2: "IC 90%" vira "faixa estimada de 90%". Tabela 5: tirar a linha do E. |
| §7.3 | Gerador sem o E (e sem o viés ×1,8); refazer a Tabela 6 e a Figura 4; "Cobertura IC 90%" vira "cobertura da faixa de 90%". |
| §7.4 | Tabela 7: tirar a coluna "Combinado"; a legenda não pode dizer que a calibração "corrige" o IrRAE. |
| §7.5 | Vira "carteira". Tabela 8: apagar "A verdade fica entre os dois limites de dependência"; cabeçalhos "IC 90%" viram "faixa estimada (cenário independente)" e "(cenário de erros alinhados)". |
| §9 | Curadoria: tirar "classificar ETFs por tema"; "ligar posições às ações (CUSIP/ISIN)" passa a depender da T-01. |
| §10 | Limitações 4 (E inflado) e 5 (combinação gaussiana) saem; próximos passos 3 ("Construir E") e 6 (calibrar) são reescritos. |
| Apêndice A | `calibracao.py` sem "combinação"; caminhos do repositório (`backend/irrae/`, `backend/ingest/`) no lugar dos caminhos do zip. |

### B. Lacunas

| ID | Tema | Decisão | Status |
|---|---|---|---|
| D-07 | Universo de empresas | Na v1.1, só empresas que entregam **10-K**. Ações da B3 e empresas que entregam 20-F (ex.: TSMC, ASML) vão para "não coberto". O 20-F tem outra numeração (risco no Item 3.D, negócio no Item 4, análise no Item 5) e fica para a v1.2. | DECIDIDO |
| D-08 | Consolidar classes da mesma empresa | No N-PORT, consolidar pelo **LEI** do emissor (GOOGL e GOOG têm o mesmo LEI). Para as empresas do escopo (50 a 100), manter uma tabela CIK ↔ LEI curada à mão, montada só com dados já permitidos (campo `lei` do N-PORT e filings da SEC). **Não usar a API do GLEIF** (EM ESPERA, seção 4). | DECIDIDO |
| D-09 | MD&A no N | Usar só a subseção "Results of Operations" do Item 7, localizada pelo título, mais o filtro de frases prospectivas. A regra "frases sobre operações do período" sai do prompt. | DECIDIDO |
| D-10 | "Descrições de segmentos" no N | **Não entram no N.** A nota de segmentos (Item 8) é a mesma evidência que o componente A já usa; contá-la duas vezes subestima a incerteza. O N lê só o Item 1 e a subseção da D-09. | DECIDIDO |
| D-11 | Amostra para revisão manual | Cerca de 200 frases, estratificadas por folha rotulada (incluindo "nenhuma folha") e por empresa. A entrega é: arquivo CSV com frase, empresa, item, rótulo automático e coluna vazia para o rótulo manual, mais um script que calcula a precisão depois que o M1 rotular. O script entra no repositório; o **CSV com frases de 10-Ks reais fica na pasta compartilhada**, fora do repositório (regra de só dados sintéticos), e só é gerado quando o e-mail do projeto existir (R-05). | DECIDIDO |
| D-12 | Alarmes da calibração | Corrigir os alarmes falsos com Bonferroni por empresa: z > Φ⁻¹(1 − 0,10 / (2m)), em que m é o número de folhas testadas na empresa. Com m = 6, o corte é z ≈ 2,39 (antes, 1,645, o que dava ~47% de chance de pelo menos um alarme falso por empresa). Referência: Dunn (1961), *JASA* 56(293). | DECIDIDO |
| D-13 | Posições vendidas dentro do ETF | No lote: vendidos num balde próprio (`vendido`, com sinal negativo) e um código de aviso; o "não coberto" nunca fica negativo; se as compradas passarem de 100% (alavancagem), aviso e nenhuma normalização. **O lote não escreve texto para o usuário.** A nota `raiox.nota_posicoes_vendidas` é da tela do produto: quem escreve é o M1, no `docs/textos_telas.md` (rascunho → aprovado), e isso não bloqueia o PR do lote. | DECIDIDO |
| D-14 | Teste 3 (ETF dentro de carteira) | Calcular os **pesos efetivos antes** e agregar uma vez só. Motivo: se a mesma empresa está na carteira direto e dentro do ETF, agregar o ETF primeiro a embaralha separadamente de si mesma no cenário independente, e a faixa sai estreita demais. | DECIDIDO |
| D-15 | Semente | A calibração usa um gerador de números aleatórios próprio, separado do gerador dos sorteios do IrRAE, para não mudar os sorteios seguintes e não quebrar os testes 1 e 2. | DECIDIDO |
| D-16 | Código do E | **Apagar** (sem flag; o histórico do Git guarda o código). A lista completa está no detalhamento abaixo da tabela. O teste 7 sai. Fechar a DT-7 no mesmo PR. | DECIDIDO |
| D-17 | Entrada do `irrae/` | Aceita ISIN e valores, para servir ao lote do MVP. No protótipo 1, a carteira do `irrae/` é só hipotética (análise e testes). Testes usam apenas ISINs sintéticos. | DECIDIDO |

**D-16 em detalhe: tudo o que é do E**

| Onde | O que fazer |
|---|---|
| `irrae/componentes.py` | Apagar `de_etfs`. |
| `irrae/agregacao.py` | Apagar `posicoes_sem_etf` e o parágrafo "Circularidade" da docstring. |
| `ingest/nport.py` | Apagar `posicoes_empresa` (classificação de ETFs por tema) e o "uso (2): componente E" da docstring. O N-PORT fica só para abrir ETFs. |
| `irrae/config/componentes.json` | Apagar `E_enquadramento` e a correlação `N_narrativa|E_enquadramento`. |
| `irrae/sintetico.py` | Apagar o E de `KAPPA_VERDADEIRO` e `P_FALTA`, a constante `HYPE`, o ramo `if k == "E_enquadramento"` e a menção ao E na docstring ("E com viés de 'hype'"). |
| `tests/irrae/test_irrae_agregacao_etf.py` | Apagar `test_sem_etf_muda_o_componente_e`. |
| `tests/ingest/test_leitores.py` | Em `test_nport`, apagar **só** a parte de `posicoes_empresa` (o import e a chamada com o assert dela). A checagem do `parse_nport` fica. |
| `tests/irrae/test_irrae_modelo.py` | Em `test_etfs_e_heranca`, apagar **só** o bloco do E (a chamada a `de_etfs` e o assert dela). A parte da herança (componente C) fica. Renomear para `test_heranca_cobertura` está aprovado. |
| `docs/matriz_de_dados.md` | **Exceção à R-03, aprovada pelo M1:** neste PR, só tirar as menções ao E: na fonte 6, o resumo ("ETFs temáticos (componente E)") e o terceiro uso do detalhe; e o ponto de atenção 7 ("especulação"). Nada mais da matriz muda. |
| `docs/divida_tecnica.md` e ADR 0004 | Fechar a DT-7 e marcar como resolvido o ponto em aberto 1 da ADR 0004 (E fora). |

A aprovação do M1 vale para apagar e editar esses testes (regra "nunca altere um teste existente só para fazê-lo passar" do `CLAUDE.md`).

**Testes de aceitação 1 e 2 (Figura 2 e Tabela 8 idênticas): como provar a regressão**

O demo usa dados reais da SEC, e o `CLAUDE.md` só permite dados sintéticos no repositório. Por isso:
1. **Fora do repositório:** rodar o demo real antes e depois de cada PR da v1.1, com a mesma semente, e colar os números no PR. Valores de referência (relatório v1): NVDA 68,98% [56,47–81,06], AMZN 19,28% [11,16–27,90]; Tabela 8: IA 30,36%, cenário independente 26,46–34,43%, erros alinhados 21,42–39,93%, não coberto 10%.
2. **No CI:** um teste de regressão com um universo **sintético congelado**. Não basta rodar o gerador com a mesma semente: sem o E, a sequência de sorteios muda e todas as empresas saem diferentes, e a reestimação de κ usa o universo inteiro. Por isso: **antes** do PR, gerar o universo uma vez, tirar o E, gravar os componentes e os resultados esperados num arquivo de teste (sintético) e usar os κ fixos do prior; **depois** do PR, recalcular sobre esse mesmo arquivo e comparar (tolerância de ponto flutuante). Escolha de engenharia do Lucas, explicada no PR.

### C. Forma do prompt

| ID | Tema | Decisão | Status |
|---|---|---|---|
| D-18 | Relatório técnico fora do repositório | O relatório é o `Relatorio_IrRAE_passo_a_passo.pdf` (v1, 26/09/2026), que o M1 envia junto com este documento. Commitar em `docs/irrae/relatorio_tecnico_v1.pdf`. O PDF diz que os números são lidos de `resultados/` por `relatorio/gerar_relatorio.py`. Commitar a partir do `irrae_prototipo (1).zip`: **`relatorio/modelo.tex` (o texto do relatório; é nele que a D-06 é aplicada)**, `relatorio/gerar_relatorio.py`, `scripts/`, `rodar_tudo.sh`, `irrae/sensibilidade.py` (Sobol, que não está no repositório), o `CLAUDE.md` do zip **renomeado** para `docs/irrae/guia_continuacao_v1.md` (com o nome `CLAUDE.md` o Claude Code o leria como instrução e ele contradiz as regras atuais) e o `FONTES.md` em `docs/irrae/FONTES_v1_historico.md`, com o aviso no topo: "Registro histórico do protótipo v1 (26/09/2026). A fonte da verdade das fontes de dados é `docs/matriz_de_dados.md`." Adaptar os scripts do zip aos caminhos atuais (`backend/ingest/`) e ao ruff é trabalho do Lucas. **`data/real/financeiro_sec.csv` e os `resultados/` do demo real ficam fora do repositório** (regra de só dados sintéticos), numa pasta compartilhada **criada pelo M1**; os scripts recebem o caminho por parâmetro. **O M1 cria essa pasta compartilhada** e envia por ela o PDF e os dados (não pelo WhatsApp). **Gerar o PDF exige XeLaTeX** com suporte a português (MiKTeX ou TeX Live, gratuitos): o Lucas instala na máquina dele, que é onde o lote roda. Gerar o PDF exige XeLaTeX com suporte a português (TeX Live ou MiKTeX, gratuitos), instalado na máquina de quem gerar o relatório. | DECIDIDO (PDF: M1; resto do zip: Lucas) |
| D-19 | Caminhos e amarras no prompt | O prompt revisado cita `backend/irrae/`, `backend/ingest/nport.py`, a ADR 0004, a DT-7, a matriz de dados, o `textos_telas.md`, a regra de teste primeiro e a aprovação para remover os testes do E (D-16). | DECIDIDO |
| D-20 | "Confirmar antes de fechar" | A lista de marcadores prospectivos do prompt (expect, anticipate, plan, intend, believe, may, will, could, aim, seek, "forward-looking") está **aprovada provisoriamente**. A seção 4 (N) pode ser implementada. O M1 vai revisar essa parte do modelo depois; por isso a lista fica num arquivo de configuração em `irrae/config/`, nunca fixa no código. | DECIDIDO (provisório) |
| D-21 | Registro da aprovação | A aprovação do M1 fica registrada na descrição de cada PR da v1.1 e numa atualização da ADR 0004 (seção "Pontos em aberto"). | DECIDIDO |

### D. Decisões extras

| ID | Tema | Decisão | Status |
|---|---|---|---|
| X-01 | Regras do `frontend/CLAUDE.md` | Restauradas ("A carteira nunca é enviada a terceiros" e "Sem analytics"). | FEITO no branch; entra na `main` com o merge do PR |
| X-02 | Faixa da carteira na tela do produto | Pela ADR 0004, o lote grava por empresa só média, P5 e P95, sem os sorteios. Com isso, a API só consegue calcular o cenário de erros alinhados (soma dos quantis ponderados). Recomendação do M1: **(a)** mostrar só essa faixa, com o nome "faixa estimada, supondo que os erros das empresas andam juntos", sem chamá-la de "conservadora"; o cenário independente fica só nos relatórios do lote. A alternativa **(b)** (gravar os sorteios e levar numpy para a API) muda arquitetura e dependências. Quando a X-02 for decidida, resolver também: (1) gravar o P5 e o P95 **do tema**, e não só das folhas, porque os quantis das folhas não somam para dar o do tema; (2) o que mostrar para empresas sem faixa (classificação de origem manual ou oficial, sem IrRAE). | CONJUNTA (Lucas) |
| X-03 | Reaproveitar o look-through do produto no `irrae/` | Para não haver duas implementações de ciclo (D-02), avaliar se o `irrae/` pode reutilizar `app/core/lookthrough.py` (a regra é que `app/` não importa `irrae/`; o contrário não está proibido). **Sim, confirmado pelo M1 e pelo Lucas em 01/10/2026**: calculando os pesos efetivos uma vez pelo `app/core` (Decimal) e convertendo para `float` só na agregação do lote. | DECIDIDO |
| X-04 | Especificação consolidada | O Lucas escreve `docs/irrae/especificacao_v1.1.md`, juntando o prompt original da v1.1 (fórmula do alarme, bootstrap, saídas (a) e (b) da carteira) com estas decisões, **sem decidir nada novo** e com cada mudança marcada pelo ID. Entra no PR de documentação aberto; o M1 confere na revisão. | APROVADO (M1 revisa no PR) |

---

## 2. Divergências entre o repositório e as decisões

| ID | Ponto | Onde no repositório | O que fazer | Status |
|---|---|---|---|---|
| R-01 | CUSIP como chave | `irrae/agregacao.py`, `pesos_da_carteira(campo="cusip")` | Depois da T-01: se ela der ≥ 95%, trocar o padrão para LEI, com ticker e nome como alternativas, e deixar o CUSIP como opção desligável. Se der bem menos, manter como está até a resposta da CGS ao formulário UOSS. **Não mudar antes da T-01.** | Aguarda T-01 |
| R-02 | "A chave de empresa é o ISIN" | `CLAUDE.md` da raiz e ADR 0003 | Funciona para ISINs brasileiros. ISINs americanos são CGS ISINs (mesma licença do CUSIP). Proposta: `empresa_id` interno, com uma tabela de identificadores (ticker, CIK, LEI, ISIN BR; CUSIP e ISIN US em campo opcional). Decisão de arquitetura. **Precisa ser decidida antes de começar a DT-3 (R-08)**, porque a DT-3 cria a tabela de emissores que a R-02 redesenha. **Usa o resultado da T-01 como insumo**: a T-01 responde só pelo lado do N-PORT; a R-02 cobre também a entrada do usuário (tickers, CSV da Avenue), a CVM e o banco. A licença CGS só fica dispensável se **nenhuma** parte do sistema guardar CUSIP ou ISIN americano. | CONJUNTA (Lucas) |
| R-03 | Matriz de dados defasada (AIPD, FSN, Patent Assignment, GLEIF, `company_tickers`, PatentsView no ODP) | `docs/matriz_de_dados.md` | ~~Não mexer. As fontes ainda aguardam autorização do M1.~~ Fontes liberadas pelo M1 em 11/10/2026; matriz atualizada (seção 4). | FEITO |
| R-04 | Duas fontes da verdade (planilha do M1 × matriz) | Planilha `Fontes_de_dados_IrRAE.xlsx` e `docs/matriz_de_dados.md` | O M1 passa os status validados para a matriz quando terminar as autorizações. O agente não altera a matriz por conta própria. | EM ESPERA |
| R-05 | E-mail do User-Agent | Matriz, ponto de atenção 3 | Precisa ser um e-mail do projeto no domínio `sagitalapp.com.br`, real e monitorado (sugestão: `dados@sagitalapp.com.br`). O M1 está criando o e-mail. **Bloqueia a T-01 até ficar pronto.** | EM EXECUÇÃO (M1) |
| R-06 | GLEIF | Fora da matriz | Liberado pelo M1 em 11/10/2026, com as condições já levantadas: licença CC0, mas proibido sugerir vínculo com o GLEIF ou usar o logo, sob multa contratual de CHF 100.000 e foro em Basileia (a ficha FP-16 da planilha não traz esta condição; ela continua valendo). | FEITO |
| R-07 | ADR 0004, ponto em aberto 3 ("faixa pelo limite comonotônico") | `docs/adr/0004-modelo-irrae.md` | Reescrever: são dois cenários de referência, nenhum é limite da faixa; o nome é "faixa estimada". Ligar com X-02. | FEITO no branch; entra na `main` com o merge do PR |
| R-08 | DT-3 × v1.1 | O produto separa classes de ações pelo ISIN (DT-3); a v1.1 consolida pela empresa | Alinhar: no lado do N-PORT, consolidar pelo LEI (D-08); no lado da B3, pelo emissor no Formulário Cadastral da CVM (já previsto na DT-3). **Prazo da DT-3: portão P3, 23/10.** | DECIDIDO |
| R-09 | Nome do produto | O README diz "Projeto RX"; o domínio é Sagital | Os sócios vão decidir. **Não alterar** README, textos nem identificadores até a decisão. | EM ANDAMENTO (sócios) |

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

## 4. ~~EM ESPERA: não implementar~~ LIBERADO em 11/10/2026

**Atualização de 11/10/2026:** o M1 liberou as fontes abaixo pela planilha de fontes
(`docs/irrae/fontes_de_dados.md`), com as condições de cada ficha (resumidas em `docs/matriz_de_dados.md`).
O texto original da seção fica abaixo, como registro.

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

1. ~~PR de documentação: R-07 e X-01.~~ **FEITO no branch** `docs/decisoes-m1-irrae-v1.1`; entra na `main` com o merge.
2. T-01, assim que o e-mail do projeto estiver criado (R-05). Em paralelo: D-18 (commitar o relatório e os arquivos do zip).
3. Decisão conjunta da R-02 (`empresa_id`), **antes de começar a DT-3**.
4. PRs da v1.1, na ordem de D-04. A lista de marcadores do N está aprovada provisoriamente (D-20). O PR que remove o E segue o detalhamento da D-16 e prova a regressão como descrito abaixo dela.
5. R-08 / DT-3 até o portão P3 (23/10), já com a estrutura decidida na R-02.
6. Depois do resultado da T-01: R-01. Depois da decisão conjunta: X-02 (com as duas lacunas listadas nela). A X-03 já está decidida e entra no PR 4.

## 6. O que o agente não decide

- Metodologia (fontes, κ, limiares, regras, taxonomia, mapeamentos, forma de apresentar): M1.
- Arquitetura, custo, dependências pesadas e o que aparece na tela: conjunta (M1 + Lucas).
- Nome do produto, e-mail do projeto e autorização de fontes: M1.

Na dúvida, pare e pergunte, citando o ID do item.
