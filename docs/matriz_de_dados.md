# Matriz de dados

Todas as fontes de dados que o Projeto RX usa ou pretende usar, com o método exato de uso de cada uma. O código só pode usar fontes com status **permitida** ou **provisória**.

A pesquisa de termos e licenças de cada fonte está em [`irrae/fontes_de_dados.md`](irrae/fontes_de_dados.md): a transcrição da planilha de fontes do M1, com uma ficha por fonte (`FP-xx`, `FA-xx`) e as normas (`BL-xx`). Em 11/10/2026 o M1 confirmou que a planilha vale como autorização dele: as fontes que as notas dele mandam usar passaram a **permitida**, com as condições da ficha. Em conflito entre esta matriz e a ficha, vale a ficha, e o conflito vai para o M1.

A planilha não é parecer jurídico. Antes do lançamento público, confirmar com advogado (aviso da própria planilha, aba Leia-me).

## Status

| Status | Significado |
|---|---|
| **permitida** | Autorizada pelo M1. Pode ser usada no produto, com as condições da ficha. |
| **provisória** | Autorizada pelo Lucas em 25/09/2026 **apenas para desenvolvimento e testes**, sem uso comercial, até a autorização do M1. |
| **pendente** | Ainda não pode ser usada. |
| **só manual** | Só consulta manual, pontual, sem automação. |
| **descartada** | Não será usada (motivo na tabela). |

## Resumo

Os números das fontes 1 a 15 são os mesmos de antes, porque outros documentos citam "fonte n".

### Fontes do produto (raio-x)

| # | Fonte | Para que serve | Licença | Ficha | Status |
|---|---|---|---|---|---|
| 1 | CVM – Composição das carteiras de fundos (CDA) | O que tem dentro de cada fundo brasileiro, inclusive os ETFs | ODbL | FP-25 | permitida |
| 2 | CVM – Cadastro de fundos | Nome, tipo e situação dos fundos | ODbL | FP-26 | permitida |
| 3 | CVM – Cadastro de companhias abertas | Setor oficial das empresas brasileiras | ODbL | FP-24 | permitida |
| 4 | CVM – Formulário Cadastral (FCA) | Ligar o ticker da B3 à empresa (CNPJ) | ODbL | fora da planilha | provisória: liberação pedida ao M1 em 11/10/2026 |
| 6 | SEC – Form N-PORT | O que tem dentro de cada ETF americano | Domínio público (SEC) | FP-09, FP-10 | provisória: o M1 pediu a explicação do uso em 11/10/2026 |
| 7 | SEC – Submissions, lista de tickers e lista SIC | Ticker americano → empresa (CIK) e setor oficial (SIC) | Domínio público (SEC) | FP-02, FP-07, FP-08 | permitida |
| 11 | Wikidata | Setor de empresas fora dos EUA e do Brasil, como preliminar | CC0 | FA-09 | permitida (só como referência cruzada) |
| 12 | Banco Central – PTAX | Câmbio do dólar | ODbL | FP-36 | permitida (só o dólar) |
| 13 | B3 – Serviço de códigos ISIN | Ligar o ticker da B3 ao ISIN | Termos da B3 | FP-31 | pendente: a nota do M1 manda usar o ISIN informado pelo usuário e, sem ele, um código interno |
| 14 | Modelo de IA (provedor a definir) | Sugerir classificações nas lacunas | Termos do provedor | – | pendente |
| 15 | Arquivos enviados pelo usuário (B3 e Avenue) | A carteira a analisar | Dado pessoal (LGPD) | – | permitida por design |
| 16 | GLEIF – LEI | Identificar a empresa pelo LEI (o N-PORT traz o LEI de cada ação) | CC0, com restrição de marca | FP-16 | permitida |
| 17 | OpenFIGI | Ligar o BDR à ação de fora que o lastreia (teste com 20 tickers) | MIT | FP-17 | permitida |
| 18 | SEC – Form N-CEN | Confirmar se um fundo americano é ETF antes de abrir | Domínio público (SEC) | FP-11 | permitida |

### Fontes do IrRAE

| # | Fonte | Componente | Licença | Ficha | Status |
|---|---|---|---|---|---|
| 5 | CVM – Formulário de Referência (FRE) | N, C, P e segmentos (Brasil) | ODbL | FP-23 | permitida |
| 8 | SEC – XBRL dos relatórios (10-K, 10-Q) | A e Ir por segmento | Domínio público (SEC) | FP-05 | permitida |
| 9 | SEC – Texto dos relatórios (10-K e 20-F) | N e plano B do Ir | Domínio público (SEC) | FP-01 | permitida |
| 10 | USPTO – PatentsView (agora no Open Data Portal) | R (titular desambiguado) | CC BY 4.0 | FP-14 | permitida (só as tabelas de titulares) |
| 19 | SEC – Financial Statement and Notes (FSN) e Financial Statement Data Sets | A por segmento, C | Domínio público (SEC) | FP-03, FP-04 | permitida |
| 20 | SEC – EDGAR Full-Text Search | N (triagem) | Domínio público (SEC) | FP-06 | permitida (só triagem) |
| 21 | USPTO – AI Patent Dataset (AIPD) | R (patentes de IA) | Domínio público | FP-12 | permitida |
| 22 | USPTO – Open Data Portal (APIs) | R | Termos da USPTO | FP-13 | permitida |
| 23 | USPTO – Patent Assignment (dataset até 2023 e XML desde 2024) | R, P | Domínio público | FP-15, FP-15b | permitida (só pessoas jurídicas) |
| 24 | NAICS | Prior setorial (opcional) | Domínio público (Census) | FP-20 | permitida |
| 25 | CVM – DFP e ITR | A, Ir (Brasil) | ODbL | FP-21, FP-22 | permitida |
| 26 | INPI – Dados abertos | R (Brasil) | Ver ficha | FP-32 | permitida (sem dados de pessoa física) |
| 27 | Receita Federal – Dados abertos do CNPJ | P, R, prior (CNAE) | Dados abertos | FP-34 | permitida (só pessoas jurídicas) |
| 28 | IBGE – CNAE | Prior setorial (Brasil) | Dado público do IBGE | FP-35 | permitida |
| 29 | OpenAlex | P&D em IA (prospectivo) | CC0 | FA-04 | permitida |
| 30 | filings.xbrl.org (ESEF) | A e Ir de empresas europeias | Ver ficha | FA-07 | permitida |
| 31 | SEC – Form 13F | Testar o modelo em carteiras de gestores | Domínio público (SEC) | FA-06 | permitida, sem guardar CUSIP (ver o ponto de atenção 11) |
| 32 | CVM – RAD / Empresas.NET | Notas de segmentos (PDF) | Termos não encontrados | FP-27 | só manual, até confirmar os termos |
| 33 | INPI – pePI | Conferência pontual de patentes | Não aceita robôs | FP-33 | só manual |
| 34 | EPO – Open Patent Services | R fora dos EUA | Termos do EPO | FA-01 | pendente: os termos permitem, o uso não foi decidido |
| 35 | Google Patents (BigQuery) | Classificar IA por CPC | CC BY 4.0 | FA-02 | pendente: risco de custo do BigQuery |

### Descartadas

| Fonte | Ficha | Motivo |
|---|---|---|
| CUSIP | FP-18 | Licença paga da CGS. Nunca guardar CUSIP nem ISIN baseado nele (`US`, `CA`); ver ADR 0005 |
| Preços diários licenciados (EUA) | FP-19 | Não são necessários na v1: o modelo roda sem preços |
| B3 – Cotações históricas, composição de índices e listas de BDRs e ETFs | FP-28, FP-29, FP-30 | Uso comercial exige licença da B3. Os ETFs vêm do CDA (fonte 1); os preços vêm do usuário |
| ANBIMA | FP-37 | Contrato pago; a CVM cobre os fundos |
| WIPO PATENTSCOPE | FA-03 | Termos proíbem automação; sem uso previsto |
| Kenneth French Data Library | FA-05 | Sem licença comercial: só estudo e calibração internos, nunca no produto |
| Taxonomia US-GAAP (arquivos do FASB) | FA-08 | Termos restritivos. Os nomes das tags que vêm nos dados da SEC podem servir de chave técnica; os rótulos e definições do FASB não são exibidos |
| sec-api.io | FA-10 | Intermediário pago; os dados originais são gratuitos na SEC |
| GICS, ICB, TRBC, BICS | FP-08 | Classificações proprietárias: exigem licença paga |
| Arquivos de composição dos emissores (ex.: iShares) | – | Termos proíbem redistribuição e trazem GICS |
| Yahoo Finance (yfinance) | FP-19 | Termos restritivos; proibido no backend |

---

## Detalhe das fontes do produto

### 1. CVM – Composição e Diversificação das Aplicações (CDA)

- **Onde:** dados.cvm.gov.br, conjunto "Fundos de Investimento: Documentos: Composição e Diversificação das Aplicações".
- **O que é:** a carteira que cada fundo brasileiro informa à CVM todo mês: cada ativo, com tipo, quantidade e valor de mercado.
- **Arquivos (FP-25):**
  - os blocos de cada mês (`cda_fi_BLC_n_AAAAMM.csv`);
  - os fundos de índice (ETFs) ficam em arquivo próprio: `cda_fiim_AAAAMM.csv`, renomeado para `cda_fie_AAAAMM.csv` a partir de 15/11/2025 (que passou a trazer também FIDC e FIAGRO);
  - as aplicações sob confidencialidade vêm consolidadas em `cda_fi_CONFID_AAAAMM.csv` e `cda_fie_CONFID_AAAAMM.csv`, sem o detalhe de cada ativo, e entram como "não coberto".
- **Atualização (FP-25):** o portal guarda os últimos 12 meses. Os 3 meses mais recentes são reapresentados todos os dias (terça a sábado, às 8h); os meses 4 a 12, toda segunda-feira.
- **Método exato:**
  1. Todo dia útil, baixamos os 3 meses mais recentes; toda semana, os demais. Uma reapresentação vira uma carga nova, e a composição vigente passa a ser a publicada por último no mesmo mês (ADR 0006, seção 3).
  2. Lemos os blocos de ativos (títulos públicos, cotas de outros fundos, ações, derivativos, depósitos etc.) e os arquivos dos ETFs.
  3. Para cada ativo, calculamos o peso = valor de mercado do ativo ÷ patrimônio líquido do fundo na mesma data.
  4. Classificamos cada ativo em um tipo: ação, fundo, caixa, derivativo, crédito, título público ou outro.
  5. Gravamos a composição de cada fundo com a data de referência, para uso no look-through.
- **Atenção:** depois da Resolução CVM 175, os fundos têm estrutura de fundo, classe e subclasse (FP-26). Conferir nos arquivos qual CNPJ identifica o fundo na composição.
- **Crédito exigido:** sim. A tela mostra algo como "Fonte: CVM, dados abertos", com texto final no `textos_telas.md`.
- **Dado pessoal:** não. São dados de fundos.
- **Atenção:** a ODbL tem cláusula de "compartilhamento pela mesma licença" para bases derivadas. Ver os pontos de atenção.

### 2. CVM – Cadastro de fundos

- **Onde:** dados.cvm.gov.br, conjunto "Fundos de Investimento: Cadastro".
- **Método exato:** baixamos o arquivo cadastral (atualizado de terça a sábado, às 8h, segundo a FP-26). Usamos CNPJ, nome, classe e situação (ativo ou cancelado) para identificar os fundos da fonte 1 e descartar os cancelados.
- **Crédito exigido:** sim, o mesmo da fonte 1.

### 3. CVM – Cadastro de companhias abertas

- **Onde:** dados.cvm.gov.br, conjunto "Companhias Abertas: Cadastro".
- **Método exato:** download mensal. Usamos o campo de setor de atividade como **setor oficial** das empresas brasileiras. Uma tabela nossa, revisada à mão, liga cada setor da CVM ao setor usado no raio-x.
- **Atenção:** a FP-24 descreve este cadastro como "chave CVM ↔ CNPJ ↔ ticker B3", mas o ticker vem da fonte 4.
- **Crédito exigido:** sim, o mesmo da fonte 1.

### 4. CVM – Formulário Cadastral (FCA)

- **Onde:** dados.cvm.gov.br, conjunto "Companhias Abertas: Documentos: Formulário Cadastral (FCA)". Licença ODbL, atualização semanal.
- **Método exato:** do pacote de cada ano, lemos **só** duas tabelas:
  - `fca_cia_aberta_valor_mobiliario`: código de negociação na B3 (ex.: PETR4), CNPJ da companhia, tipo do valor mobiliário (ON, PN, unit, BDR), mercado e datas de listagem. É o que liga o ticker do CSV da B3 à empresa e junta as classes da mesma empresa (DT-3);
  - `fca_cia_aberta_geral`: setor de atividade e situação da companhia.
- **Não traz o ISIN** (conferido no dicionário de dados da CVM em 11/10/2026). A ligação com o ISIN fica para a fonte 13 ou para o ISIN informado pelo usuário.
- **Dado pessoal:** o mesmo pacote traz `fca_cia_aberta_dri`, `fca_cia_aberta_departamento_acionistas` e `fca_cia_aberta_endereco`, com nome, CPF, e-mail e telefone de pessoas. **Esses arquivos nunca são importados** (LGPD).
- **Crédito exigido:** sim, o mesmo da fonte 1.

### 6. SEC – Form N-PORT

- **Onde:** SEC EDGAR, formulário N-PORT-P de cada fundo e ETF americano (FP-10). Para muitos ETFs de uma vez, os conjuntos em lote (FP-09).
- **O que é:** a carteira completa que cada fundo americano informa à SEC. É publicada a cada trimestre, com cerca de 60 dias de defasagem.
- **Método exato:**
  1. Para cada ETF necessário, baixamos o N-PORT mais recente (arquivo XML), lido só por `ingest/xml_seguro.ler_xml`.
  2. De cada posição lemos: nome, LEI do emissor, valor, percentual do patrimônio, tipo de ativo e, para derivativos, o ativo-objeto.
  3. A ação é ligada à empresa pelo LEI ou, sem LEI, pelo nome exato (ADR 0005, seção 6).
  4. Gravamos a composição com a data de referência.
- **Nunca guardado nem exibido:** CUSIP e ISIN americano. O XML traz os dois, mas eles só passam pela memória durante a leitura (ADR 0005, confirmado pelo M1 em 11/10/2026). O campo "Inhouse Asset ID" não é usado: na maior parte das linhas é o próprio CUSIP.
- **Dois usos:**
  - composição dos ETFs americanos da carteira do usuário;
  - **aproximação dos ETFs UCITS:** um ETF UCITS (listado na Europa) é aproximado pelo ETF americano que segue o mesmo índice, e a tela mostra um rótulo de aproximação.
- **Regras de acesso da SEC (BL-03):** `User-Agent` com o nome do projeto e o e-mail do projeto (ponto de atenção 3) e no máximo 10 requisições por segundo.
- **Marca (BL-02):** citar a SEC como fonte, sem usar o nome "SEC" ou o logo do EDGAR de forma que sugira vínculo.
- **Risco (FP-09):** em 02/2026 a SEC propôs flexibilizar a divulgação do N-PORT; a frequência ou a defasagem podem mudar.
- **Frequência:** trimestral.

### 7. SEC – Submissions, lista de tickers e lista SIC

- **Onde:** data.sec.gov (API de submissões por empresa), o arquivo `company_tickers.json` e a lista de códigos SIC.
- **Método exato:**
  1. A lista de tickers liga o ticker americano à empresa na SEC (CIK). **O CIK é a chave; o ticker é só um atributo**: a própria SEC não garante que o arquivo esteja correto ou completo (FP-07).
  2. As submissões trazem o **código SIC** da empresa (ex.: 5961 = varejo por catálogo e internet). Para muitas empresas, baixamos o arquivo único `submissions.zip`, republicado toda noite (FP-02), em vez de uma consulta por empresa.
  3. Uma tabela nossa, revisada à mão, liga cada um dos cerca de 400 códigos SIC a um setor do raio-x.
- **Frequência:** mensal.
- **Regras de acesso e marca:** as mesmas da fonte 6.

### 11. Wikidata

- **Onde:** serviço público de consultas do Wikidata (query.wikidata.org) ou os dumps completos, para volume grande.
- **Método exato:** para empresas sem código SIC nem registro na CVM, consultamos o ISIN (propriedade P946) e a indústria (propriedade P452). Uma tabela nossa liga cada indústria do Wikidata a um setor do raio-x. Essas classificações recebem o selo **"preliminar"**.
- **Condições (FA-09):** só como referência cruzada, nunca como fonte oficial: o conteúdo é colaborativo e pode estar errado ou desatualizado. CNPJ e participações se confirmam com a CVM ou a Receita. `User-Agent` com contato é obrigatório. Só dados de empresas (o Wikidata também tem pessoas).
- **Licença:** CC0 (domínio público). Crédito não exigido; vamos citar a fonte mesmo assim.
- **Frequência:** mensal.

### 12. Banco Central do Brasil – PTAX

- **Onde:** API de dados abertos do BCB (serviço PTAX no portal Olinda).
- **Método exato:** para a data da análise, buscamos a PTAX de venda de fechamento do dólar. Se a data não for dia útil, usamos o último dia útil anterior. Se o BCB não tiver cotação nesse dia, voltamos mais um dia. A tela mostra a PTAX usada e a data dela.
- **Licença:** ODbL, indicada na página do conjunto de dados no portal de dados abertos do BCB (conferido em 12/10/2026). Exige crédito, como a fonte 1.
- **Condições (FP-36):** só a PTAX do dólar, que o BCB apura (as outras moedas vêm de terceiros). **O aviso de responsabilidade que vem nas respostas da API Olinda deve ser repassado ao usuário.** A resposta da API e a página do conjunto não trazem esse aviso (conferido em 12/10/2026): falta o M1 indicar a fonte do texto (`cambio.aviso_bcb` em `textos_telas.md`).
- **Frequência:** hoje, a cada análise, com cache diário (DT-1); com o banco, uma carga diária.

### 13. B3 – Serviço de códigos ISIN (pendente)

- **Método previsto:** consultar o serviço de ISIN da B3 para ligar ticker e ISIN.
- **Nota do M1 (FP-31):** usar o ISIN informado pelo próprio usuário no CSV; se vier um ticker sem ISIN, criar um código interno. O sufixo `F` (ex.: BBDC3F) é o mercado fracionário do mesmo papel, não outro ativo. No protótipo 1, o ISIN do CSV só é usado em memória durante a análise, como toda a carteira (confirmado pelo M1 em 11/10/2026).

### 14. Modelo de IA (pendente)

- **Uso previsto:** sugerir setor, tema e subtema para empresas que não tenham classificação em nenhuma outra fonte. Enviamos ao modelo apenas dados públicos da empresa (nome, descrição, país). **Nunca enviamos dados de usuários.**
- Tudo o que a IA sugere entra com status "rascunho" e aparece com o selo "preliminar" até a revisão humana.
- **A definir:** o provedor e os termos de uso do conteúdo gerado.

### 15. Arquivos enviados pelo usuário

- **O que é:** o CSV exportado da área do investidor da B3 ou da Avenue, ou o cadastro manual.
- **Método exato:** o arquivo é lido e processado **só em memória** durante a requisição e descartado em seguida. Nada da carteira é gravado no banco nem registrado em log. As mensagens de erro não repetem os valores do arquivo.
- **Dado pessoal:** sim (LGPD). O único dado pessoal gravado pelo projeto é o e-mail da lista de espera, com a data e a versão do aviso de privacidade aceito.

### 16. GLEIF – LEI

- **Onde:** golden copy (arquivos completos) ou a API do GLEIF.
- **Uso:** identificar a empresa pelo LEI, que o N-PORT traz em cada ação (ADR 0005, `empresa_id` `LEI:`), e ligar LEI a grupos econômicos no IrRAE.
- **Condições (FP-16 e R-06 das decisões do M1):** licença CC0, mas é proibido usar o logo do GLEIF ou sugerir vínculo com ele, sob multa contratual de CHF 100.000 e foro em Basileia.

### 17. OpenFIGI

- **Uso:** teste com 20 tickers de BDR para ligar cada um à ação estrangeira que o lastreia (FP-29); se funcionar, vira o método de BDRs.
- **Condições (FP-17):** licença MIT. Limites da API sem chave: 25 consultas de mapeamento por minuto, com até 10 itens por consulta; com chave gratuita, 25 a cada 6 s, com até 100 itens. A chave, se usada, fica fora do repositório.

### 18. SEC – Form N-CEN

- **Uso:** confirmar se um fundo americano é ETF, e que índice segue, antes de abrir a carteira dele pela fonte 6.
- **Regras de acesso e marca:** as mesmas da fonte 6.

---

## Detalhe das fontes do IrRAE

As condições de cada uma estão na ficha. Os pontos que mudam o método:

- **Fonte 8 (XBRL):** conferir a soma dos segmentos contra o consolidado. A API `companyfacts` traz os campos `label` e `description`, que são textos da taxonomia do FASB: não exibi-los; usar rótulos próprios em português.
- **Fonte 9 (texto dos relatórios):** quando faltar o dado da fonte 8, contamos as menções a palavras-chave de cada subtema nas seções "Business" e "Management's Discussion and Analysis" do relatório mais recente. Citar a SEC e a empresa como fonte.
- **Fonte 10 (PatentsView):** baixar **só as tabelas de titulares** (assignees), nunca as de inventores (pessoas físicas). Crédito CC BY 4.0: quem criou (USPTO PatentsView), a licença com link, um link para a fonte e um aviso de que os dados foram modificados. Migrou para o Open Data Portal em 20/03/2026.
- **Fontes 21 a 23 (USPTO):** creditar a USPTO e citar a documentação de cada dataset, sem logo nem selo. Download pelos arquivos em lote do Open Data Portal, nunca pelas interfaces web. Patent Assignment: o dataset tabulado cobre até 2023 e o XML, de 2024 em diante, com importação mensal; separar cessões, fusões e mudanças de nome de garantias, licenças e ônus; conferir a junção 2023/2024; descartar pessoas físicas na ingestão.
- **Fonte 24 (NAICS):** se usar a API do Census, exibir o aviso exigido pela ficha FP-20.
- **Fontes 26 e 27 (INPI e Receita):** apagar CPF e dados de pessoa física já na ingestão. Da Receita, filtrar pelo universo de interesse, excluir empresário individual e MEI, não guardar a tabela de sócios nem e-mail e telefone; crédito "Fonte: Receita Federal, Dados Abertos do CNPJ".
- **Fonte 28 (IBGE):** baixar a estrutura da CNAE uma vez e guardar localmente; crédito "Fonte: IBGE/CONCLA, CNAE 2.3" (conferir a versão vigente).
- **Fonte 29 (OpenAlex):** API com chave gratuita, ou o snapshot público para volume grande. Não republicar resumos nem textos dos artigos; dados agregados por instituição, sem nomes de autores.

---

## Pontos de atenção para o M1

1. **ODbL (CVM).** Além do crédito, a ODbL exige que uma base de dados derivada, se usada publicamente, seja compartilhada pela mesma licença. A nota da FP-29 entende que gráficos e escores exibidos no produto contam como "trabalho produzido" e pedem só o aviso de atribuição. Confirmar com advogado antes do lançamento público.
2. **N-PORT (fonte 6):** o M1 pediu em 11/10/2026 a explicação do uso, para decidir a liberação.
3. **Contato no `User-Agent`** da SEC e do Wikimedia: o M1 está criando o e-mail do projeto (R-05). Sem ele, nenhum acesso automatizado à SEC pode rodar.
4. **FCA (fonte 4):** liberação pedida ao M1 em 11/10/2026, lendo só as tabelas de valores mobiliários e geral.
5. **B3:** dados da B3 não são usados na v1 (FP-28 a FP-31). A planilha cita a Política Comercial de Market Data v3.0.4; segundo o revisor da planilha, uma política nova vale desde 01/01/2026. Atualizar a referência antes de qualquer uso de dados da B3.
6. **Créditos e avisos na tela:** CVM (ODbL), PTAX (o aviso do Banco Central) e, quando usadas, as fontes do IrRAE (detalhe acima). SEC e GLEIF: citar como fonte, sem logo e sem sugerir vínculo. Textos finais no `textos_telas.md`.
7. **IA:** definir o provedor e verificar os termos sobre o conteúdo gerado.
8. **Riscos das fontes de composição:** a SEC (02/2026) e a CVM propuseram flexibilizar a divulgação das carteiras ao mercado. Se isso mudar o que é publicado, a frequência ou a defasagem das fontes 1 e 6 podem piorar.
9. **CDI como referência de renda fixa:** segundo o revisor da planilha, a Taxa DI é apurada pela B3. O protótipo 1 não mostra rentabilidade; vale só para depois.
10. **Fontes pendentes:** EPO (fonte 34) e Google Patents (fonte 35).
11. **CUSIP no 13F (fonte 31):** a nota da FA-06 sugere mapear à mão CUSIP → ticker de poucos ativos (ex.: ADRs brasileiros). Isso guardaria CUSIP, o que contraria a FP-18 e o ADR 0005. Decidir: o 13F sem nenhum CUSIP guardado, ou uma exceção registrada no ADR 0005.
12. **Uso atual:** as fontes permitidas podem ir ao produto, com as condições da ficha; as provisórias continuam só em desenvolvimento e testes. O lançamento público depende da confirmação jurídica do ponto 1 e do aviso da planilha.
