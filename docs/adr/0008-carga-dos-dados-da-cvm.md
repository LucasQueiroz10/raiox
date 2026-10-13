# ADR 0008: Carga dos dados da CVM (composições dos fundos)

- **Status:** proposto. O plano foi enviado ao M1 em 12/10/2026, em PDF, para discussão antes da
  aprovação. Passa a "aceito" quando o M1 responder sobre as regras marcadas com "decidir" (seção 4)
  e as perguntas da seção 7.
- **Data:** 2026-10-12
- **Decisor:** Lucas (Membro 2), pela engenharia. O M1 decide as regras de tradução que mudam o que
  o usuário vê (seção 4) e os pontos de produto (seção 7).
- **Relacionados:** ADR 0005 (identificação), ADR 0006 (banco e cargas), ADR 0007 (cargas agendadas),
  matriz de dados (fontes 1 a 4), DT-1, DT-3 e DT-12.

## Contexto

A API, o motor e o banco estão prontos, mas o banco está vazio e a API ainda responde com o conjunto
de exemplo sintético (7 empresas e 3 fundos inventados). Uma carteira comum de testador (um ETF de
Ibovespa, um fundo multimercado e ações da Petrobras) sairia quase vazia: os fundos como "não aberto"
e as ações sem setor. A meta do P3 é cobrir pelo menos 60% das carteiras dos testadores.

A CVM publica todo mês a carteira de todos os fundos brasileiros, inclusive dos ETFs da B3 (CDA,
fonte 1 da matriz, liberada pelo M1 em 11/10/2026). A carga baixa esses arquivos, traduz cada linha
para o formato do motor e grava no banco.

### O que os arquivos reais mostram

Análise do mês de agosto de 2026, feita em 12/10/2026 só com contagens, sem ler registros:

| Achado | Consequência |
|---|---|
| Cerca de 25,5 mil classes de fundos e 530 mil linhas de aplicações por mês | Volume tranquilo para o banco |
| Desde a Resolução CVM 175, o fundo é identificado pelo CNPJ da **classe** (`CNPJ_FUNDO_CLASSE`, com máscara `99.999.999/9999-99`) | Esse CNPJ vira o `fundo_id` (`CNPJ:` + 14 caracteres) |
| Os 205 ETFs ficam no arquivo `cda_fie_AAAAMM.csv`, junto com FIDCs e FIAGROs | A carga lê também esse arquivo |
| No bloco de ações (`BLC_4`) vêm o ticker (`CD_ATIVO`) e o ISIN (`CD_ISIN`): 316 tickers de ações, cada um com um ISIN só, sem conflito | O ISIN continua sendo a chave da ação (seção 1) |
| No arquivo dos ETFs vem só o ticker, sem ISIN. 97% das linhas de ação com ticker acham o ISIN pelo bloco de ações | O ticker dos ETFs é traduzido pelo bloco de ações |
| Das 626 linhas de ação de ETF sem ticker, 623 trazem o CNPJ da empresa emissora (`CPF_CNPJ_EMISSOR`, tipo PJ) | Ligação direta à empresa (`BR:CNPJ:`) |
| Os blocos 6 e 8 e o arquivo dos ETFs têm `CPF_CNPJ_EMISSOR` com `PF_PJ_EMISSOR`: 4 linhas com CPF de pessoa física em agosto | O CPF nunca é gravado (LGPD) |
| Cerca de 10,6 mil classes têm parte da carteira confidencial (arquivos `CONFID`, só com o total por tipo de aplicação) | Não se sabe o que é essa parte |
| 43 fundos com patrimônio negativo | O peso de cada item (valor ÷ patrimônio) perde o sentido |
| Cerca de 53 mil linhas de fundos offshore (`BLC_7`), sem composição pública | Expôs o defeito da DT-12 |
| Cerca de 127 mil linhas de debêntures no `BLC_4`, sem o CNPJ de quem emitiu | Entram como crédito, sem ligar à empresa |
| Arquivos em latin-1, separador `;`, números com ponto decimal e sinal negativo (futuros, valores a pagar) | O leitor usa `csv` e `Decimal`, nunca `float` |

## Decisões

### 1. Identificação

- **Ação brasileira:** o ISIN continua sendo o `ativo_id` (ADR 0005, sem mudança). No arquivo dos ETFs,
  o ticker é traduzido para o ISIN pelos pares ticker ↔ ISIN do bloco de ações do mesmo mês. Sem esse
  par, a linha liga direto à empresa pelo CNPJ do emissor (`BR:CNPJ:`), como o item do N-PORT sem
  ticker (ADR 0005, seção 2). Somadas as duas ligações, 97% das linhas de ação dos ETFs ficam
  identificadas.
- **Ação no exterior** (`BLC_7`) negociada na NYSE, na Nasdaq ou na AMEX: `US:` + ticker. Em outras
  bolsas: sem identificador ("não identificado").
- **Fundo:** `CNPJ:` + o CNPJ da classe. Cotas de outros fundos (`BLC_2`) apontam para o
  `CNPJ_FUNDO_CLASSE_COTA` e são abertas em cadeia.

### 2. Peso

Peso de cada item = valor de mercado (`VL_MERC_POS_FINAL`) ÷ patrimônio líquido da classe na mesma
data (arquivo `PL`; no arquivo dos ETFs, `VL_PATRIM_LIQ` da própria linha), em `Decimal` de 50 dígitos
(ADR 0006, seção 4).

### 3. O que fica de fora

- O CPF de emissor pessoa física: o item entra sem emissor. Nunca é gravado.
- As posições confidenciais não entram; como o peso é calculado sobre o patrimônio inteiro, o valor
  delas aparece sozinho como "não identificado" (decidir a forma de mostrar: seção 7).
- Os fundos com patrimônio menor ou igual a zero ficam fora da carga, com registro no log da carga.

### 4. Tradução de cada linha

**A decidir com o M1** (proposta e motivo):

| No CDA | Proposta | Por quê |
|---|---|---|
| Operações compromissadas | Caixa | Empréstimos de curtíssimo prazo (em geral de um dia) garantidos por título público: na prática, dinheiro em caixa |
| Disponibilidades, valores a pagar e a receber | Caixa (pode ser negativo) | Contas do próprio fundo; valores a pagar reduzem o caixa |
| Ações recebidas em empréstimo | Ação com peso negativo (vendido) | O fundo pegou ações emprestadas e vendeu: aposta contra a empresa, que o motor já mostra à parte |
| Debêntures | Crédito, sem empresa ligada | O bloco não traz o CNPJ de quem emitiu; dá para melhorar depois |
| Fundos offshore | Fundo não aberto, com aviso | Sem composição pública; depende da correção da DT-12 |
| Posições confidenciais | Não entram (viram não identificado) | Não se sabe o que são |
| Fundos com patrimônio menor ou igual a zero | Fora da carga, com registro | Pesos sem sentido |

**Diretas:**

- Ações, units e ações cedidas em empréstimo: ação, pelo ISIN.
- Cotas de outros fundos: fundo, pelo CNPJ da classe investida.
- Títulos públicos: título público.
- CDB, letra financeira e outros títulos de banco: crédito, com o banco como emissor (`CNPJ_EMISSOR`).
- Opções, futuros e swaps: derivativo.

### 5. Frequência

Todo dia, os 3 meses mais recentes (a CVM os republica com correções de terça a sábado); os demais,
toda semana (matriz, fonte 1; horários no ADR 0007, seção 5). Uma reapresentação vira uma carga nova,
e a composição vigente passa a ser a publicada por último no mesmo mês (ADR 0006, seção 3).

### 6. Etapas, um PR por vez e com teste primeiro

1. **Motor:** um fundo sem identificador dentro de outro fundo vira "não aberto", com aviso, em vez de
   derrubar a análise. Fecha a DT-12.
2. **Leitor do CDA** (`ingest/cvm_cda.py`, sem banco): lê o zip do mês e devolve as composições pelas
   regras da seção 4. Testes com arquivos sintéticos no formato da CVM (latin-1, `;`).
3. **Carga no banco** (pacote novo `cargas/`): uma rotina comum a todas as cargas (abrir, preparar em
   tabela temporária, validar, publicar ou registrar o erro) e o comando `python -m cargas.cvm`, que
   baixa os 3 meses recentes ou lê um zip local. Testes com banco.
4. **Identificação e setor:** FCA (ticker → CNPJ da empresa; só as tabelas de valores mobiliários e
   geral, nunca os arquivos com dados pessoais), os pares ticker ↔ ISIN do bloco de ações e o cadastro
   de companhias (setor oficial, com o nome usado pela CVM; a tabela de tradução para os setores do
   raio-x vem depois). Liga cada ação à empresa e fecha a DT-3. Depende da liberação do FCA.
5. **PTAX no banco:** carga diária; fecha a DT-1.

Meta: etapas 1 a 5 entre 13 e 18/10, deixando 19 a 23/10 para o P3 (HTTPS, telas, importação de CSV e
testes).

### 7. Pontos pedidos ao M1

1. As regras "a decidir" da seção 4.
2. Posições confidenciais na tela: junto com "não identificado" ou numa categoria própria
   ("confidencial"). As duas opções de texto já estão em `docs/textos_telas.md`.
3. Debêntures sem emissor: aceitável para o P3, ou procurar o emissor em outra fonte antes.
4. Liberações: o FCA (etapa 4), o N-PORT e o e-mail do projeto para o acesso à SEC.
5. Defasagem: carteiras com algumas semanas de atraso, com a data na tela, servem para o P3.

## Consequências

- **O que melhora:** cerca de 25,5 mil fundos e 205 ETFs reais em vez de 3 fictícios; empresa
  escondida e classes somadas (PETR3 e PETR4) com dados reais; atualização diária; fundo offshore sem
  derrubar a análise; câmbio do banco. A meta do P3 fica viável para a parte brasileira das carteiras.
- **O que não cobre:** ETFs e ações americanas (N-PORT e SEC, que esperam o e-mail do projeto e a
  liberação do N-PORT); BDRs (teste com o OpenFIGI); temas (IrRAE, depois do P3).
- **O que fica sem identificar:** cerca de 3% das ações dentro dos ETFs, as posições confidenciais e as
  debêntures sem emissor.
- **ADR 0005:** a seção 6 (composições da CVM) passa a apontar para este ADR.

## Alternativas descartadas

- **Trocar a chave da ação brasileira para o ticker** (`B3:` + ticker): o bloco de ações já liga cada
  ticker a um ISIN, sem conflito, então a chave do ADR 0005 se mantém.
- **Composição dos ETFs pela B3:** exige licença de dados (fichas FP-29 e FP-30 da planilha do M1); o
  CDA traz os ETFs de graça, com licença aberta.
- **Ler o CDA com pandas:** converteria valores para `float`; o leitor usa `csv` e `Decimal`.
