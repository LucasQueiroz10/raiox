# ADR 0008: Carga dos dados da CVM (composições dos fundos)

- **Status:** aceito em 12/10/2026. O plano foi enviado ao M1 em 12/10/2026, em PDF, e aprovado por ele
  no mesmo dia, com os ajustes da seção 7.
- **Data:** 2026-10-12. Revisado no mesmo dia com a resposta do M1 e com a conferência dos sinais e do
  empréstimo de ações nos arquivos de agosto de 2026.
- **Decisor:** Lucas (Membro 2), pela engenharia. O M1 decidiu as regras de tradução que mudam o que
  o usuário vê (seção 4) e os pontos de produto (seção 7).
- **Relacionados:** ADR 0005 (identificação), ADR 0006 (banco e cargas), ADR 0007 (cargas agendadas),
  matriz de dados (fontes 1 a 4), DT-1 e DT-3. A DT-12 foi fechada pela etapa 1 (PR #65).

## Contexto

A API, o motor e o banco estão prontos, mas o banco está vazio e a API ainda responde com o conjunto
de exemplo sintético (7 empresas e 3 fundos inventados). Uma carteira comum de testador (um ETF de
Ibovespa, um fundo multimercado e ações da Petrobras) sairia quase vazia: os fundos como "não aberto"
e as ações sem setor. Não há meta fixa de cobertura: a base deve abrir e identificar o máximo possível
das carteiras (decisão do Lucas em 12/10/2026, no lugar da meta de 60% do plano enviado ao M1).

A CVM publica todo mês a carteira de todos os fundos brasileiros, inclusive dos ETFs da B3 (CDA,
fonte 1 da matriz, liberada pelo M1 em 11/10/2026). A carga baixa esses arquivos, traduz cada linha
para o formato do motor e grava no banco.

### O que os arquivos reais mostram

Análise do mês de agosto de 2026, feita em 12/10/2026 só com contagens e somas, sem olhar nenhum
fundo pelo nome:

| Achado | Consequência |
|---|---|
| Cerca de 25,5 mil classes de fundos e 530 mil linhas de aplicações por mês | Volume tranquilo para o banco |
| Desde a Resolução CVM 175, o fundo é identificado pelo CNPJ da **classe** (`CNPJ_FUNDO_CLASSE`, com máscara `99.999.999/9999-99`) | Esse CNPJ vira o `fundo_id` (`CNPJ:` + 14 caracteres) |
| Os 205 ETFs ficam no arquivo `cda_fie_AAAAMM.csv`, junto com FIDCs e FIAGROs | A carga lê também esse arquivo |
| No bloco de ações (`BLC_4`) vêm o ticker (`CD_ATIVO`) e o ISIN (`CD_ISIN`): 316 tickers de ações, cada um com um ISIN só, sem conflito | O ISIN continua sendo a chave da ação (seção 1) |
| No arquivo dos ETFs vem só o ticker, sem ISIN. 97% das linhas de ação com ticker acham o ISIN pelo bloco de ações | O ticker dos ETFs é traduzido pelo bloco de ações |
| Das 626 linhas de ação de ETF sem ticker, 623 trazem o CNPJ da empresa emissora (`CPF_CNPJ_EMISSOR`, tipo PJ) | Ligação direta à empresa (`BR:CNPJ:`) |
| Os blocos 6 e 8 e o arquivo dos ETFs têm `CPF_CNPJ_EMISSOR` com `PF_PJ_EMISSOR`: 4 linhas com CPF de pessoa física em agosto | O CPF nunca é gravado (LGPD) |
| Cerca de 10,6 mil classes têm parte da carteira confidencial (arquivos `CONFID`, só com o total por tipo de aplicação) | Entra numa categoria própria, "confidencial" (seção 3) |
| 43 fundos com patrimônio negativo | O peso de cada item (valor ÷ patrimônio) perde o sentido |
| Cerca de 53 mil linhas de fundos offshore (`BLC_7`), sem composição pública | Expôs o defeito da DT-12, corrigido na etapa 1 |
| Cerca de 127 mil linhas de debêntures no `BLC_4`, sem o CNPJ de quem emitiu, mas todas com um código no `CD_ATIVO` (como PETR16) | Entram como crédito, sem ligar à empresa; o código permite ligar depois (seção 4) |
| Os passivos vêm com valor **positivo**: valores a pagar (29 mil linhas positivas e 1 negativa), obrigações por ações recebidas em empréstimo, opções lançadas, diferencial de swap a pagar, obrigações a termo e outras operações passivas. Somando as linhas como vêm, 80% dos fundos batem com o patrimônio dentro de 1%; com os passivos negativos, 97,9% | O leitor troca o sinal dos passivos (seção 4) |
| As ações cedidas em empréstimo aparecem só na linha própria, não também em "Ações": nos 188 fundos com essas linhas, a soma bate com o patrimônio contando-as (mediana 100,4%) e fica em 81% sem elas | Entram como ação comprada, sem contagem dupla (conferência pedida pelo M1) |
| Não há linha de "ações recebidas em empréstimo": vem a **obrigação** de devolver a ação (`Obrigações por ações e outros TVM recebidos em empréstimo`), sempre positiva | Com o sinal trocado, vira a posição vendida. Se o fundo ainda tem a ação, ela aparece em "Ações" e as duas linhas se anulam |
| O código das ações no exterior (`CD_ATIVO_BV_MERC`) vem misturado: ticker com o código da bolsa (como "AAPL US"), números de 1 a 7 dígitos e siglas | Só código com formato de ticker é aproveitado; o resto é descartado (seção 1) |
| Arquivos em latin-1, separador `;`, números com ponto decimal | O leitor usa `csv` e `Decimal`, nunca `float` |

## Decisões

### 1. Identificação

- **Ação brasileira:** o ISIN continua sendo o `ativo_id` (ADR 0005, sem mudança). No arquivo dos ETFs,
  o ticker é traduzido para o ISIN pelos pares ticker ↔ ISIN do bloco de ações do mesmo mês. Sem esse
  par, a linha liga direto à empresa pelo CNPJ do emissor (`BR:CNPJ:`), como o item do N-PORT sem
  ticker (ADR 0005, seção 2). Somadas as duas ligações, 97% das linhas de ação dos ETFs ficam
  identificadas.
- **Ação no exterior** (`BLC_7`) negociada na NYSE, na Nasdaq ou na AMEX: `US:` + ticker, só quando o
  código tem formato de ticker (sozinho ou seguido do código da bolsa, como "AAPL US"). Qualquer outro
  código (ISIN, CUSIP, SEDOL, número interno) é descartado na leitura e nunca gravado (ADR 0005; pedido
  do M1). Em outras bolsas, ou sem código aproveitável: sem identificador ("não identificado").
- **Fundo:** `CNPJ:` + o CNPJ da classe. Cotas de outros fundos (`BLC_2`) apontam para o
  `CNPJ_FUNDO_CLASSE_COTA` e são abertas em cadeia.
- **ETF ou fundo na carteira do usuário:** o usuário informa o ETF pelo ticker ou pelo ISIN, mas a
  composição está no CNPJ da classe. Nenhuma fonte liberada liga um ao outro hoje; a etapa 4 procura essa
  ligação no próprio CDA e no cadastro de fundos (fonte 2).

### 2. Peso

Peso de cada item = valor de mercado (`VL_MERC_POS_FINAL`, com o sinal da seção 4) ÷ patrimônio líquido
da classe na mesma data (arquivo `PL`; no arquivo dos ETFs, `VL_PATRIM_LIQ` da própria linha), em
`Decimal` de 50 dígitos (ADR 0006, seção 4).

### 3. O que fica de fora e o que entra à parte

- **CPF de emissor pessoa física:** o item entra sem emissor. Nunca é gravado. Antes de publicar cada
  carga, uma varredura procura números com formato de CPF (11 dígitos com dígito verificador válido)
  nas linhas preparadas; se achar, a carga não publica (pedido do M1).
- **Posições confidenciais:** entram numa categoria própria, "confidencial", pelo valor líquido de cada
  fundo (soma das linhas do `CONFID`, com os passivos negativos) ÷ patrimônio. Não se juntam ao "não
  identificado", que fica só para o que não conseguimos ligar (M1; FP-25: o omitido conta como não
  coberto). Decisão do Lucas sobre o valor líquido em 12/10/2026.
- **Fundos com patrimônio menor ou igual a zero:** ficam fora da carga, com registro no log da carga.
  A carga guarda só o registro de que o fundo existe sem composição utilizável, para a tela avisar
  "fundo sem composição utilizável" quando ele estiver na carteira do usuário, em vez do aviso genérico
  de fundo sem composição (M1).

### 4. Tradução de cada linha

**Decididas com o M1 em 12/10/2026:**

| No CDA | Tradução | Condição ou motivo |
|---|---|---|
| Operações compromissadas | Caixa | Empréstimos de curtíssimo prazo garantidos por título público: na prática, dinheiro em caixa |
| Disponibilidades, valores a pagar e a receber | Caixa, com os valores a pagar negativos | Contas do próprio fundo |
| Obrigações por ações recebidas em empréstimo | Ação com valor negativo (vendido) | O fundo pegou ações emprestadas e vendeu. Sem contagem dupla com o bloco de ações (achados) |
| Debêntures | Crédito, sem empresa ligada | Aceito para o P3, com o total de crédito sem emissor separado na tela. Depois do P3: ligar pelo código da debênture (ex.: PETR16) à emissora; nunca pela ANBIMA (FP-37) |
| Fundos offshore | Fundo sem identificador: não aberto, com aviso | Sem composição pública (etapa 1) |
| Posições confidenciais | Categoria "confidencial", pelo valor líquido | Seção 3 |
| Fundos com patrimônio menor ou igual a zero | Fora da carga, com registro e aviso na tela | Seção 3 |

**Sinal:** o CDA informa os passivos com valor positivo. O leitor troca o sinal de valores a pagar,
obrigações por ações recebidas em empréstimo, opções lançadas, diferencial de swap a pagar, obrigações
por compra a termo a pagar, obrigações por venda a termo a entregar e outras operações passivas e
exigibilidades. Os futuros já vêm com o sinal do ajuste.

**Diretas:**

- Ações, units e ações cedidas em empréstimo: ação, pelo ISIN.
- Cotas de outros fundos: fundo, pelo CNPJ da classe investida.
- Cotas de ETF ou FII cedidas em empréstimo (bloco 8): fundo, pelo CNPJ do emissor, que é o próprio
  fundo, como no arquivo dos ETFs (14/10/2026). As cotas recebidas em empréstimo (a obrigação de
  devolver, posição vendida) ficam como fundo sem identificador até a decisão da DT-16.
- Títulos públicos: título público.
- CDB, letra financeira e outros títulos de banco: crédito, com o banco como emissor (`CNPJ_EMISSOR`).
- Opções, futuros e swaps: derivativo (opções lançadas com valor negativo).

Os tipos que não aparecem acima (BDRs, títulos do agronegócio, CRIs, termo, outras aplicações) seguem a
mesma lógica. A tabela completa, tipo a tipo e com o sinal, fica no código do leitor (etapa 2), com
teste, e vai ao M1 na revisão do PR.

### 5. Frequência

De terça a sábado às 9h, os 3 meses mais recentes (a CVM os republica com correções nesses dias, às
8h); os demais, toda semana (matriz, fonte 1; horários no ADR 0007, seção 5). Uma reapresentação vira
uma carga nova, e a composição vigente passa a ser a publicada por último no mesmo mês (ADR 0006,
seção 3).

### 6. Etapas, um PR por vez e com teste primeiro

1. **Motor** (feita, PR #65): um fundo sem identificador dentro de outro fundo vira "não aberto", com
   aviso, em vez de derrubar a análise. Fechou a DT-12.
2. **Leitor do CDA**, em dois PRs:
   1. **Motor, API e banco:** a categoria "confidencial"; o crédito sem emissor separado na resposta; os
      avisos de composição com mais de 90 dias e de fundo sem composição utilizável. Mexe em mais de um
      módulo: plano aprovado antes.
   2. **Leitor** (`ingest/cvm_cda.py`, sem banco): lê o zip do mês e devolve as composições pelas regras
      das seções 1 a 4. Testes com arquivos sintéticos no formato da CVM (latin-1, `;`).
3. **Carga no banco** (pacote novo `cargas/`): uma rotina comum a todas as cargas (abrir, preparar em
   tabela temporária, validar, publicar ou registrar o erro) e o comando `python -m cargas.cvm`, que
   baixa os 3 meses recentes ou lê um zip local. Antes de publicar, a carga confere:
   - se o download deu certo e se os arquivos e as colunas são os esperados. Uma mudança de nome ou de
     layout (como a troca de `cda_fiim` para `cda_fie` em 15/11/2025) faz a carga não publicar e
     dispara o alerta (ADR 0007, seção 8);
   - a varredura de CPF (seção 3);
   - a soma das linhas de cada fundo contra o patrimônio (seção 8, item a).

   Testes com banco.
4. **Identificação e setor**, em três PRs (levantamento e decisões de 13/10/2026):
   1. **Cadastro no banco** (`python -m cargas.cadastro`, toda segunda): FCA (ticker → CNPJ e o setor
      oficial, com o nome usado pela CVM; só as tabelas de valores mobiliários e geral, nunca os
      arquivos com dados pessoais), os pares ticker ↔ ISIN do CDA, as cotas de ETF e FII
      emprestadas (ticker → CNPJ) e o informe mensal de FII (fonte 36, liberada pelo M1 em
      13/10/2026: ISIN, tipo e segmento). A raiz do ticker, que é o código do emissor na B3, liga
      ticker e ISIN à companhia; o que as fontes não ligam fica na curadoria versionada
      (`backend/cargas/curadoria/`). Ação sem ISIN conhecido usa o código interno `B3:` + ticker
      (ADR 0005). O setor vem do FCA, e o cadastro de companhias (fonte 3) fica de fora, porque
      traz dados pessoais do responsável. A tabela que traduz para os setores do raio-x vem depois.
      Com os dados de 13/10/2026: 771 companhias com setor e 96,3% do valor das ações dentro dos
      fundos ligado a uma companhia (o resto são BDRs, 3,7%, e 0,1% de empresas pequenas).
   2. **Entrada por ticker e por CNPJ** no `POST /api/raiox` (ADR 0005, seção 5).
   3. **FIIs no raio-x:** a categoria "Fundos imobiliários", com o tipo de cada FII (regra em
      `backend/ingest/cvm_fii.py`), em vez de "não aberto". Feita em 14/10/2026: vale para o FII
      direto e para o FII dentro de fundos, que o CDA traz no bloco de cotas de fundos com o CNPJ
      (agosto de 2026: 2.840 linhas, R$ 47,8 bi; nenhuma no bloco de ações). A resposta da API
      traz as fatias por tipo e, no tijolo, por segmento (`fiis_por_tipo`). No PR seguinte, as
      cotas de ETF e FII cedidas em empréstimo (bloco 8) passaram a apontar para o CNPJ do fundo
      (agosto de 2026: R$ 3,6 bi, quase tudo em ETFs). Os "R$ 140 mi de FII emprestado" citados no
      desenho eram quase todos obrigações por cotas recebidas em empréstimo, que ficam na DT-16.

   Sem os PRs 4.2 e 4.3, o ETF, o fundo e o FII da carteira do usuário não são abertos.
5. **PTAX no banco:** carga diária; fecha a DT-1.

Meta: etapas 2 a 5 entre 13 e 18/10, deixando 19 a 23/10 para o P3 (HTTPS, telas, importação de CSV e
testes). Se faltar tempo, a prioridade é o que abre as carteiras (2.2, 3 e 4); o PR 2.1 pode ficar por
último.

### 7. Resposta do M1 (12/10/2026)

1. **Regras da seção 4:** aprovadas, com as condições anotadas na tabela. A conferência do empréstimo
   de ações que ele pediu está nos achados.
2. **Confidenciais na tela:** categoria própria, com o texto proposto por ele (`raiox.nota_confidencial`
   em `docs/textos_telas.md`).
3. **Debêntures sem emissor:** aceitáveis no P3, com o total de crédito sem emissor separado na tela.
4. **Liberações:**
   - FCA, só as tabelas de valores mobiliários e geral;
   - N-PORT, com a condição já prevista no ADR 0005: ligar pelo LEI e nunca gravar CUSIP nem ISIN fora
     da lista permitida (que já exclui US e CA). Entra depois desta carga;
   - o e-mail do projeto, para o `User-Agent` da SEC. O endereço fica fora do repositório, numa
     variável de ambiente da carga.
5. **Defasagem:** serve para o P3. A data de cada composição fica visível. Composição com mais de 90 dias
   continua aberta, com o aviso "sem composição recente", nunca com um mês antigo sem aviso (decisão do
   Lucas em 12/10/2026 sobre abrir com aviso).
6. **O que faltou no plano:**
   - o crédito à CVM no rodapé da tela do raio-x (`avisos.creditos_fontes`);
   - a PTAX com crédito ao Banco Central, o aviso dele e só o dólar (já feito: `cambio.aviso_bcb` e
     `app/dados/ptax.py`);
   - ISIN e CUSIP descartados nas ações no exterior (seção 1);
   - o alerta quando o download falhar ou o arquivo mudar (etapa 3).
7. **Rotinas:** as da seção 5 e do ADR 0007. As manuais do M1 ficam no roteiro de operação
   (`docs/runbooks/producao.md`).

### 8. Verificações

**Automáticas:**

- **a) Soma de cada fundo:** a soma das linhas (com os passivos negativos e a parte confidencial, sem o
  resíduo "não identificado") contra o patrimônio. O relatório da carga lista os fundos fora de 1%, sem
  bloquear a publicação. O resíduo fica de fora porque, por definição, completa 100%. Em agosto de 2026,
  97,9% dos fundos ficaram dentro de 1%.
- **b) Nenhum CPF gravado:** a varredura da seção 3, antes de publicar.
- **c) PETR3 e PETR4 numa empresa só:** teste com dados sintéticos na etapa 4 e conferência depois da
  primeira carga real.
- **d) Mês republicado:** a versão nova vale na API e a anterior fica guardada (ADR 0006, seção 3;
  testes com banco na etapa 3).
- **e) Carteira da seção 1, ponta a ponta** (ETF de Ibovespa, multimercado e PETR4): um script em
  `backend/medicoes/`, com os códigos passados na hora de rodar (nenhuma carteira no código), mede
  quanto da carteira foi aberto e identificado. Sem meta fixa.
- **f) PTAX em fim de semana e feriado:** já coberto pelos testes de `app/core/cambio.py`; a resposta
  traz a data da cotação usada.

**Manuais (M1, uma vez antes do P3):**

- **g)** Conferir à mão 3 fundos, um deles ETF, contra a carteira divulgada pelo gestor (só consulta;
  nada é importado de lá).
- **h)** Testar a importação com o CSV da B3 dele, no app rodando. A carteira real não entra no
  repositório nem nos testes: os testes do importador usam um CSV sintético no mesmo formato.

## Consequências

- **O que melhora:** cerca de 25,5 mil fundos e 205 ETFs reais em vez de 3 fictícios; empresa
  escondida e classes somadas (PETR3 e PETR4) com dados reais; atualização de terça a sábado; fundo
  offshore sem derrubar a análise; parte confidencial à vista; câmbio do banco.
- **O que não cobre:** ETFs e ações americanas (o N-PORT foi liberado em 12/10/2026, mas entra depois
  desta carga); BDRs (teste com o OpenFIGI); temas (IrRAE, depois do P3).
- **O que fica sem identificar:** cerca de 3% das ações dentro dos ETFs e as debêntures sem emissor. As
  posições confidenciais aparecem à parte.
- **ADR 0005:** a seção 6 (composições da CVM) passa a apontar para este ADR.
- **ADR 0007:** a carga da CDA e o aquecimento passam a rodar de terça a sábado.

## Alternativas descartadas

- **Trocar a chave da ação brasileira para o ticker** (`B3:` + ticker): o bloco de ações já liga cada
  ticker a um ISIN, sem conflito, então a chave do ADR 0005 se mantém.
- **Composição dos ETFs pela B3:** exige licença de dados (fichas FP-29 e FP-30 da planilha do M1); o
  CDA traz os ETFs de graça, com licença aberta.
- **Ler o CDA com pandas:** converteria valores para `float`; o leitor usa `csv` e `Decimal`.
- **Somar as linhas com o sinal do arquivo:** só 80% dos fundos fechariam com o patrimônio, e os
  passivos apareceriam como aplicações.
- **Juntar as posições confidenciais ao "não identificado":** descartada pelo M1. "Não identificado" fica
  só para o que não conseguimos ligar.
