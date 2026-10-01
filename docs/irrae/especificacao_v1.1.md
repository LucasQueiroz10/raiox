# Especificação consolidada: IrRAE v1.1

- **Status:** consolidação (X-04). Não decide nada novo.
- **Fontes:**
  1. Prompt "IrRAE v1 → v1.1: carteira fundamental, sem Enquadramento" (M1, 30/09/2026), gerado sem
     acesso ao repositório.
  2. `docs/decisoes_m1_irrae_v1.1.md` (versão 4, aprovada em 01/10/2026), que corrige o prompt item a item.
- **Como ler:** o texto segue o prompt. Onde uma decisão mudou o prompt, o trecho traz o ID entre
  colchetes, por exemplo [D-02]. Em caso de conflito, vale o documento de decisões. O que nenhum dos dois
  resolve está na seção 9 (pendências) e não deve ser implementado sem resposta.
- **Regras do projeto que continuam valendo:** `CLAUDE.md` da raiz e `backend/CLAUDE.md`, ADR 0004
  (governança), `docs/matriz_de_dados.md` (fontes) e `docs/textos_telas.md` (qualquer texto de tela)
  [D-19].

## Objetivo

O usuário entrega uma carteira; ela é decomposta em ações; cada ação tem a exposição calculada **só com
fundamentos da própria empresa**; a saída é a faixa de exposição da carteira por tema e subtema. É
exposição fundamental, não sensibilidade de mercado (β). As saídas do lote e os relatórios usam esse
rótulo; na tela do produto, só textos do `docs/textos_telas.md` [D-19].

- **Protótipo 1:** a carteira do `irrae/` é só hipotética (análise e testes). A carteira do usuário
  continua sendo calculada em memória pela API [D-17].
- **Universo:** só empresas que entregam 10-K. Ações da B3 e empresas que entregam 20-F (ex.: TSMC, ASML)
  vão para "não coberto"; o 20-F fica para a v1.2 [D-07].

## Ordem dos PRs [D-04]

| PR | Conteúdo | Situação em 01/10/2026 |
|---|---|---|
| 1 | Remover o E (seção 2) | Feito no branch `feat/irrae-sem-enquadramento` |
| 2 | Calibração vira auditoria (seção 3) | A fazer |
| 3 | Filtro do N (seção 4) | A fazer (a amostra real depende da R-05) |
| 4 | Agregação da carteira e teste 5 novo (seções 1 e 5) | A fazer |
| 5 | Relatório e changelog (seção 6) | Adiado para depois do protótipo 1 (DT-8) |

## 1. Entrada e look-through

- **Entrada:** ISIN, tipo (`acao`, `etf`, `caixa`, `outro`) e valor [D-17, D-03]. O prompt pedia
  identificador por ticker, CUSIP ou ISIN e peso como fração do patrimônio. O CUSIP fica de fora até o
  resultado da T-01 [D-03, R-01]. Testes usam só ISINs sintéticos [D-17].
- **Validação (prompt):** valores não negativos; com valores, os pesos (valor / total) somam 1 por
  construção. Posição vendida ou alavancagem **direta** do usuário está fora do escopo da v1.1 e dá erro
  claro.
- **Look-through recursivo (ETF dentro de ETF):**
  `ω_i^ef = ω_i^direto + Σ_e ω_e · ω_{i|e}`
  - Calculado pelo `app/core/lookthrough.py` (em `Decimal`), convertido para `float` só na agregação do
    lote [X-03; ver DT-9].
  - Os pesos efetivos são calculados **antes** e a agregação é feita uma vez só [D-14].
  - Ciclo de ETFs: segue a regra do produto, recalcula até a diferença ficar abaixo de 0,1%
    (`CONVERGENCIA_CICLO`) e manda o resto para "não aberto". **Sem erro** [D-02]. A profundidade e o
    número de passos seguem as travas do `app/core`.
  - Posições do N-PORT, que fica só para abrir ETFs [D-16]. A saída registra a data-base das posições
    (atraso de ~60 dias).
- **Classes da mesma empresa** (ex.: GOOGL/GOOG): consolidar pelo **LEI** do emissor no N-PORT, com uma
  tabela CIK ↔ LEI curada à mão para as empresas do escopo, montada só com dados já permitidos. Sem a API
  do GLEIF [D-08]. O prompt pedia consolidar pelo CIK.
- **Vendidos dentro do ETF** [D-13]: balde próprio `vendido`, com sinal negativo, e um código de aviso. O
  "não coberto" nunca fica negativo. Se as compradas passarem de 100% (alavancagem), aviso e nenhuma
  normalização. O lote não escreve texto para o usuário.
- **Balde `nao_coberto`:** caixa, ações sem IrRAE, ETF sem N-PORT, derivativos e empresas fora do universo
  [D-07]. **Não é núcleo nem 0% de IA**: é reportado à parte.

## 2. Remover o componente E [D-16] (PR 1)

O E media o rótulo que o mercado dá à ação, não a atividade da empresa, e era circular. Apagado sem flag;
o histórico do Git guarda o código. A lista completa está no detalhamento da D-16; o teste de aceitação 7
sai.

- Fusão: **nenhuma fórmula muda**. A eq. 9 já impõe Σp = 1 entre as fontes presentes, e `p_igual`
  continua uniforme entre as fontes reais presentes.
- Regra "percepção não cria tema": o pilar Percepção passa a ser só {N}, logo `σ_a^perc = p_N · m_{N,a}`
  [D-05].

## 3. Calibração por retornos vira auditoria (PR 2)

- A combinação por precisão (eq. 19) sai do cálculo da exposição: o IrRAE final é o fundamental.
- `calibracao.py` continua igual por dentro: estilo de Sharpe com NNLS aumentado, bootstrap em blocos de
  20 dias, fatores de empresas puras (≥ 60% na folha, **sempre** excluindo a empresa analisada) e fator do
  núcleo = índice do setor oficial.
- Saída como diagnóstico separado, por folha: `m^f` e `β̂`, cada um com a sua faixa estimada (nunca
  "IC" [D-01]), e alerta de divergência quando
  `z = |m^f − β̂| / sqrt(v^f + v^m) > Φ⁻¹(1 − 0,10 / (2m))`,
  em que m é o número de folhas testadas na empresa (com m = 6, z > 2,39) [D-12]. O prompt usava 1,645.
- **O diagnóstico nunca altera F.**
- A calibração usa um gerador de números aleatórios próprio, separado do gerador dos sorteios do IrRAE
  [D-15].
- Sem preços disponíveis, o módulo é pulado sem erro.

## 4. N restrito ao negócio atual (PR 3)

- **Texto usado:** Item 1 (Business) e, no Item 7, só a subseção "Results of Operations", localizada pelo
  título [D-09]. As descrições de segmentos **não** entram, porque são a mesma evidência do componente A
  [D-10].
- O Item 1A (Risk Factors) fica fora do N; continua alimentando só a exposição negativa (eq. 16), fora do
  simplex.
- **Filtro de frases prospectivas:** marcadores expect, anticipate, plan, intend, believe, may, will,
  could, aim, seek e "forward-looking", mais o bloco de safe harbor. A lista está aprovada
  **provisoriamente** e fica num arquivo de configuração em `irrae/config/`, nunca fixa no código [D-20].
- **Contagem (como hoje):** rótulos múltiplos repartidos, `n_0 = n_total − Σ n_a`,
  `x ∼ Dir(n + α_0)`, `α_0 = 0,5`. κ⁰_N = 6 e o N continua no pilar Percepção [D-05].
- **Revisão manual** [D-11]: cerca de 200 frases, estratificadas por folha rotulada (incluindo "nenhuma
  folha") e por empresa. O script entra no repositório; o CSV (frase, empresa, item, rótulo automático e
  coluna vazia para o rótulo manual) fica na pasta compartilhada, fora do repositório, e só é gerado
  quando o e-mail do projeto existir (R-05). Outro script calcula a precisão depois que o M1 rotular.

## 5. Agregação da carteira (PR 4; generaliza a eq. 20)

`E^(s) = Σ_{i∈C} ω_i^ef · F_i^(s) + (1 − Σ_{i∈C} ω_i^ef) · e_nao_coberto` (ver a pendência P-1)

- A média é exata (linearidade).
- **Dois cenários de referência, nenhum é limite da faixa** [D-01, R-07]:
  - independente: permutações independentes dos sorteios de cada ação;
  - erros alinhados (comonotônico): **por área escalar** (cada folha e cada tema separadamente), ordenar
    os sorteios de cada ação e somar posto a posto, o que equivale a `Q(p) = Σ ω_i Q_i(p)`. Reportar
    como faixa, não como vetor de sorteios.
- Nomes nas saídas e relatórios: "faixa estimada (cenário independente)" e "faixa estimada (cenário de
  erros alinhados)". Nunca "IC", "IC90", "intervalo de confiança" nem "limite". O mesmo vale para a faixa
  por ação [D-01].
- Mesmo S e semente registrada para todas as ações.
- **Saídas:**
  - (a) por tema e subtema: média, as duas faixas estimadas de 90% e o % não coberto;
  - (b) por ação: `ω^ef`, IrRAE (média e faixa estimada), contribuição `ω · média`, parcela da variância
    `ω_i² Var(F_i) / Σ_j ω_j² Var(F_j)` e selo.
- **Correções no código atual** [D-01]: em `test_comonotonico_mais_largo_e_quantis_somam`, sai a checagem
  de largura e fica a de que os quantis somam; na docstring de `irrae/agregacao.py`, "casos-limite" vira
  "cenários de referência" e sai "A verdade fica entre os dois".
- **Tela do produto:** decisão conjunta pendente (X-02).

## 6. Ajustes secundários: relatório (PR 5, adiado; DT-8)

- Experimento sintético (seção 7.3): o gerador já está sem o E e sem o viés ×1,8 (PR 1); falta reexecutar
  a Tabela 6 e a Figura 4.
- Sobol: não tem entradas ligadas ao E.
- Relatório: as mudanças, seção por seção, estão na D-06 (inclui 7.1, 7.4, 10 e o Apêndice A). Changelog
  v1.1 item a item.
- Arquivos do zip a trazer para o repositório: D-18.

## 7. O que não muda (prompt)

Taxonomia e árvore, linha de mapeamento (eq. 3), componentes A, Ir, B, R, C, P e prior, eqs. 7 a 12,
estimação de κ (5.6), regras (5.7), papel e exposição negativa (5.8), Kalman (5.11) e cadeia (5.12).

## 8. Testes de aceitação

1. **Regressão do demo real** (Figura 2 idêntica com a mesma semente; ex.: NVDA 68,98% [56,47–81,06],
   AMZN 19,28% [11,16–27,90]): roda **fora do repositório**, antes e depois de cada PR, e os números vão
   no PR. No CI, a regressão usa o universo sintético congelado (`tests/irrae/test_irrae_regressao.py`)
   [detalhe da D-16].
2. **Carteira = ETF hipotético da seção 7.5** (NVDA 20%, MSFT 18%, AMZN 15%, GOOGL 15%, META 12%, ORCL 10%,
   9% sem IrRAE, 1% caixa) reproduz a Tabela 8: IA 30,36%, cenário independente 26,46–34,43%, erros
   alinhados 21,42–39,93%, não coberto 10%. Também fora do repositório.
3. Carteira com um ETF dentro dá o mesmo resultado que a carteira "achatada" equivalente, com os pesos
   efetivos calculados antes [D-14].
4. Ciclo de ETFs **converge** e o resto vai para "não aberto" [D-02]. O prompt pedia erro.
5. Em cada sorteio do cenário independente: Σ folhas + não coberto = 1 (ver P-1) e subtema ≤ tema. Em toda
   área (folha e tema), com tolerância de 1e-9, só de ponto flutuante [D-01]:
   - variância dos erros alinhados ≥ variância do cenário independente;
   - média dos 5% maiores sorteios (k = ⌈0,05·S⌉): erros alinhados ≥ independente;
   - média dos 5% menores sorteios: erros alinhados ≤ independente.

   O prompt pedia "largura comonotônica ≥ largura independente", que é falso em geral (contraexemplo na
   D-01).
6. Sem preços: o pipeline roda completo e a calibração é pulada.
7. ~~Com o E desligado, nenhuma chamada à classificação de ETFs.~~ Sai: o E foi apagado [D-16].
8. N: uma frase prospectiva de teste não é contada, e uma frase do Item 1A não entra no N.

## 9. Pendências que esta consolidação encontrou (perguntar antes de implementar)

- **P-1 (PR 4, M1):** com o balde `vendido` da D-13, a fórmula de `E^(s)` e a identidade do teste 5
  ("Σ folhas + não coberto = 1") precisam incluir o vendido? O prompt foi escrito antes da D-13.
- **P-2 (PR 4, Lucas):** como representar uma posição direta de tipo `caixa` ou `outro`, que pode não ter
  ISIN, já que a entrada da D-17 é por ISIN.

Pendências que já estão no documento de decisões: R-05 (e-mail do projeto, bloqueia a T-01 e a amostra
real do N), R-01 (depois da T-01), R-02 (antes da DT-3), X-02 (tela) e R-09 (nome do produto).
