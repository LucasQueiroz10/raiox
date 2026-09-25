# Matriz de dados

Todas as fontes de dados que o Projeto RX usa ou pretende usar, com o método exato de uso de cada uma. O código só pode usar fontes com status **permitida** ou **provisória**.

**Para o M1:** cada fonte precisa de validação da licença e dos termos de uso. Os pontos marcados com **(a confirmar)** são o nosso entendimento e ainda não foram verificados nos termos oficiais. A seção [Pontos de atenção](#pontos-de-atenção-para-o-m1) reúne o que mais pede análise jurídica.

## Status

| Status | Significado |
|---|---|
| **permitida** | Validada pelo M1. Pode ser usada no produto. |
| **provisória** | Autorizada pelo Lucas em 25/09/2026 **apenas para desenvolvimento e testes do modelo, sem uso comercial**, até a validação do M1. |
| **pendente** | Ainda não pode ser usada. |
| **descartada** | Não será usada (motivo na tabela). |

## Resumo

| # | Fonte | Para que serve | Licença | Status |
|---|---|---|---|---|
| 1 | CVM – Composição das carteiras de fundos (CDA) | O que tem dentro de cada fundo brasileiro | ODbL | provisória |
| 2 | CVM – Cadastro de fundos | Dados cadastrais dos fundos (CNPJ, nome, tipo) | ODbL | provisória |
| 3 | CVM – Cadastro de companhias abertas | Setor oficial das empresas brasileiras | ODbL | provisória |
| 4 | CVM – Formulário Cadastral (valores mobiliários) | Ligar código de negociação da B3 ao ISIN | ODbL | provisória |
| 5 | CVM – Formulário de Referência | Componente Ir do IrRAE para empresas brasileiras (futuro) | ODbL | pendente |
| 6 | SEC – Form N-PORT | O que tem dentro de cada ETF americano; ETFs temáticos (componente E) | Domínio público | provisória |
| 7 | SEC – EDGAR Submissions e lista de tickers | Setor oficial (código SIC) das empresas registradas na SEC | Domínio público | provisória |
| 8 | SEC – XBRL dos relatórios anuais (10-K) | Receita e investimento por segmento (componentes A e Ir) | Domínio público | provisória |
| 9 | SEC – Texto dos relatórios anuais (10-K e 20-F) | Plano B do componente Ir | Domínio público | provisória |
| 10 | USPTO – PatentsView | Patentes por empresa e área (componente R) | CC BY 4.0 (a confirmar) | provisória |
| 11 | Wikidata | Setor de empresas fora dos EUA e do Brasil | CC0 | provisória |
| 12 | Banco Central – PTAX | Câmbio do dólar | Dados abertos do BCB (a confirmar) | provisória |
| 13 | B3 – Tabela de códigos ISIN | Ligar ticker da B3 ao ISIN (alternativa à fonte 4) | Termos da B3 (a confirmar) | pendente |
| 14 | Modelo de IA (provedor a definir) | Sugerir classificações nas lacunas | Termos do provedor | pendente |
| 15 | Arquivos enviados pelo usuário (B3 e Avenue) | A carteira a analisar | Dado pessoal (LGPD) | permitida por design |
| – | GICS, ICB, TRBC, BICS | Classificações setoriais | Proprietárias | **descartada**: exige licença paga |
| – | Arquivos de composição dos emissores (ex.: iShares) | Composição de ETFs com setor GICS | Termos restritivos | **descartada**: termos proíbem redistribuição e trazem GICS |
| – | Yahoo Finance (yfinance) | – | Termos restritivos | **descartada**: proibida no backend |

---

## Detalhe de cada fonte

### 1. CVM – Composição e Diversificação das Aplicações (CDA)

- **Onde:** portal de dados abertos da CVM (dados.cvm.gov.br), conjunto "Fundos de Investimento: Documentos: Composição e Diversificação das Aplicações".
- **O que é:** a carteira que cada fundo brasileiro informa à CVM todo mês: cada ativo, com tipo, quantidade e valor de mercado.
- **Método exato:**
  1. Uma vez por mês, baixamos o arquivo compactado do mês mais recente publicado.
  2. Lemos os blocos de ativos (títulos públicos, cotas de outros fundos, ações, derivativos, depósitos etc.).
  3. Para cada ativo, calculamos o peso = valor de mercado do ativo ÷ patrimônio líquido do fundo na mesma data.
  4. Classificamos cada ativo em um tipo: ação, fundo, caixa, derivativo, crédito, título público ou outro.
  5. Gravamos no nosso banco a composição de cada fundo com a data de referência, para uso no look-through.
- **Frequência:** mensal.
- **Crédito exigido:** sim. A tela mostra algo como "Fonte: CVM, dados abertos", com texto final no `textos_telas.md`.
- **Dado pessoal:** não. São dados de fundos.
- **Atenção:** a ODbL tem cláusula de "compartilhamento pela mesma licença" para bases derivadas. Ver os pontos de atenção.

### 2. CVM – Cadastro de fundos

- **Onde:** dados.cvm.gov.br, conjunto "Fundos de Investimento: Cadastro".
- **Método exato:** download mensal do arquivo cadastral. Usamos CNPJ, nome, classe e situação (ativo ou cancelado) para identificar os fundos da fonte 1 e descartar os cancelados.
- **Frequência:** mensal.
- **Crédito exigido:** sim, o mesmo da fonte 1.

### 3. CVM – Cadastro de companhias abertas

- **Onde:** dados.cvm.gov.br, conjunto "Companhias Abertas: Cadastro".
- **Método exato:** download mensal. Usamos o campo de setor de atividade como **setor oficial** das empresas brasileiras. Uma tabela nossa, revisada à mão, liga cada setor da CVM ao setor usado no raio-x.
- **Frequência:** mensal.
- **Crédito exigido:** sim, o mesmo da fonte 1.

### 4. CVM – Formulário Cadastral: valores mobiliários

- **Onde:** dados.cvm.gov.br, conjunto "Companhias Abertas: Documentos: Formulário Cadastral (FCA)".
- **Método exato:** download anual e a cada atualização. Usamos a lista de valores mobiliários de cada companhia para ligar o código de negociação da B3 (ex.: PETR4) ao ISIN da ação. É a chave usada para ler o CSV da B3 enviado pelo usuário.
- **(a confirmar):** se o arquivo traz o ISIN de cada código de negociação. Se não trouxer, a alternativa é a fonte 13.
- **Crédito exigido:** sim, o mesmo da fonte 1.

### 5. CVM – Formulário de Referência (futuro)

- **Método previsto:** contar menções a palavras-chave de cada tema nas seções de atividades e de investimentos, como componente Ir do IrRAE para empresas brasileiras sem registro na SEC. Ainda não será usado.

### 6. SEC – Form N-PORT

- **Onde:** SEC EDGAR (sec.gov), formulário N-PORT-P de cada fundo e ETF americano.
- **O que é:** a carteira completa que cada fundo americano informa à SEC. É publicada trimestralmente, com cerca de 60 dias de defasagem.
- **Método exato:**
  1. Para cada ETF necessário, localizamos o registro dele no EDGAR e baixamos o N-PORT mais recente (arquivo XML).
  2. Lemos cada posição: nome, identificadores (ISIN quando houver), valor, percentual do patrimônio, tipo de ativo e, para derivativos, o ativo-objeto e o valor nocional.
  3. Gravamos a composição com a data de referência.
- **Três usos:**
  - composição dos ETFs americanos da carteira do usuário;
  - **aproximação dos ETFs UCITS:** um ETF UCITS (listado na Europa) é aproximado pelo ETF americano que segue o mesmo índice, e a tela mostra um rótulo de aproximação;
  - **componente E do IrRAE:** peso de cada empresa nos ETFs temáticos (ex.: ETFs de IA) e nos ETFs setoriais.
- **Regras de acesso da SEC:** identificação obrigatória no cabeçalho `User-Agent` (nome do projeto e um e-mail de contato) e no máximo 10 requisições por segundo.
- **Frequência:** trimestral.
- **Crédito:** não exigido. Vamos citar a fonte mesmo assim.

### 7. SEC – EDGAR Submissions e lista de tickers

- **Onde:** data.sec.gov (API de submissões por empresa) e o arquivo público de tickers da SEC.
- **Método exato:**
  1. A lista de tickers liga o ticker americano ao identificador da empresa na SEC (CIK).
  2. A API de submissões devolve o **código SIC** da empresa (ex.: 5961 = varejo por catálogo e internet).
  3. Uma tabela nossa, revisada à mão, liga cada um dos cerca de 400 códigos SIC a um setor do raio-x.
- **Frequência:** mensal.
- **Regras de acesso:** as mesmas da fonte 6.

### 8. SEC – XBRL dos relatórios anuais (10-K)

- **Onde:** SEC EDGAR, arquivos XBRL que acompanham cada 10-K.
- **Método exato:** do relatório anual mais recente de cada empresa, lemos a **receita por segmento de negócio** (componente A do IrRAE) e, quando informados, o **investimento (capex) e as aquisições por segmento** (componente Ir). Uma tabela nossa liga cada segmento a um subtema (ex.: segmento de nuvem → Cadeia de IA › Nuvem) ou ao núcleo da empresa.
- **Frequência:** anual, por empresa.
- **Regras de acesso:** as mesmas da fonte 6.

### 9. SEC – Texto dos relatórios anuais (10-K e 20-F)

- **Método exato:** quando faltar o dado da fonte 8, contamos as menções a palavras-chave de cada subtema nas seções "Business" e "Management's Discussion and Analysis" do relatório mais recente. O componente Ir passa a ser a fatia de menções de cada área. A lista de palavras-chave é nossa e versionada.
- **Frequência:** anual, por empresa.

### 10. USPTO – PatentsView

- **Onde:** patentsview.org (API e arquivos em massa do escritório de patentes dos EUA).
- **Método exato:**
  1. Buscamos as patentes concedidas nos últimos 3 anos em nome de cada empresa, pelo nome do titular.
  2. Pelas classes técnicas de cada patente (classificação CPC), atribuímos a patente a um subtema (ex.: CPC G06N, aprendizado de máquina → Cadeia de IA › Modelos) ou ao núcleo.
  3. O componente R é a fatia de patentes em cada área.
- **(a confirmar):** a licença (entendemos que é CC BY 4.0, o que exige crédito) e se a API exige chave de acesso. Se exigir, a chave fica fora do repositório.
- **Frequência:** trimestral.

### 11. Wikidata

- **Onde:** serviço público de consultas do Wikidata (query.wikidata.org).
- **Método exato:** para empresas sem código SIC nem registro na CVM, consultamos o ISIN (propriedade P946) e a indústria (propriedade P452). Uma tabela nossa liga cada indústria do Wikidata a um setor do raio-x. Essas classificações recebem o selo **"preliminar"**, porque o conteúdo é colaborativo.
- **Licença:** CC0 (domínio público). Crédito não exigido; vamos citar a fonte mesmo assim.
- **Regras de acesso:** identificação no `User-Agent`, conforme a política de uso do Wikimedia.
- **Frequência:** mensal.

### 12. Banco Central do Brasil – PTAX

- **Onde:** API de dados abertos do BCB (serviço PTAX no portal Olinda) e SGS, série 1 (dólar, venda).
- **Método exato:** para a data da análise, buscamos a PTAX de venda de fechamento do dólar. Se a data não for dia útil, usamos o último dia útil anterior. Se o BCB não tiver cotação nesse dia, voltamos mais um dia. O valor fica guardado em cache no próprio dia. A tela mostra a PTAX usada e a data dela.
- **(a confirmar):** os termos de uso dos dados abertos do BCB e se exigem citação.
- **Frequência:** a cada análise, com cache diário.

### 13. B3 – Tabela de códigos ISIN (pendente)

- **Método previsto:** baixar a tabela pública de códigos ISIN da B3 para ligar ticker e ISIN, caso a fonte 4 não traga essa informação.
- **(a confirmar):** os termos de uso da B3 permitem esse uso? A B3 costuma restringir o uso comercial dos seus dados.

### 14. Modelo de IA (pendente)

- **Uso previsto:** sugerir setor, tema e subtema para empresas que não tenham classificação em nenhuma outra fonte. Enviamos ao modelo apenas dados públicos da empresa (nome, descrição, país). **Nunca enviamos dados de usuários.**
- Tudo o que a IA sugere entra com status "rascunho" e aparece com o selo "preliminar" até a revisão humana.
- **A definir:** o provedor e os termos de uso do conteúdo gerado.

### 15. Arquivos enviados pelo usuário

- **O que é:** o CSV exportado da área do investidor da B3 ou da Avenue, ou o cadastro manual.
- **Método exato:** o arquivo é lido e processado **só em memória** durante a requisição e descartado em seguida. Nada da carteira é gravado no banco nem registrado em log. As mensagens de erro não repetem os valores do arquivo.
- **Dado pessoal:** sim (LGPD). O único dado pessoal gravado pelo projeto é o e-mail da lista de espera, com a data e a versão do aviso de privacidade aceito.

---

## Pontos de atenção para o M1

1. **ODbL (CVM).** Além do crédito, a ODbL exige que uma base de dados derivada, se usada publicamente, seja compartilhada pela mesma licença. Precisamos saber se a nossa tabela de composições e as agregações se enquadram como base derivada, e o que isso exige.
2. **ISIN de empresas americanas contém o CUSIP.** O CUSIP é licenciado pela CUSIP Global Services. Usar ISINs americanos que vêm do N-PORT, uma fonte pública, é permitido para o nosso caso?
3. **Contato no `User-Agent`** da SEC e do Wikimedia: precisamos de um e-mail de contato do projeto, e não um e-mail pessoal.
4. **PatentsView:** confirmar a licença e o crédito exigido.
5. **B3:** confirmar se a tabela de ISIN e a classificação setorial da B3 podem ser usadas.
6. **Banco Central:** confirmar os termos dos dados abertos.
7. **Componente "especulação" do IrRAE:** usa a presença das empresas em ETFs temáticos. É um nome interno. Na tela, o nome será neutro (ex.: "associação pelo mercado"), para não parecer julgamento sobre a empresa.
8. **IA:** definir o provedor e verificar os termos sobre o conteúdo gerado.
9. **Uso atual:** todas as fontes provisórias estão sendo usadas apenas em desenvolvimento e testes, sem comercialização. Qualquer lançamento público depende da validação desta matriz.
