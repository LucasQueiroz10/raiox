Fonte: documento "VITRINE_front.md", recebido pelo Lucas e transcrito em 10/11/2026. Decisão de
seguir com a vitrine: ADR 0009.

## Correções da conferência de 10/11/2026

O texto original vem abaixo, sem mudanças. Onde ele diverge do repositório, vale esta lista e o
ADR 0009:

1. **Autoria:** a vitrine é um projeto conjunto do Lucas e do M1, e não de uma pessoa só. A marca
   Sagital continua.
2. **V-02 já resolvida:** o N-PORT (FP-09, FP-10) foi liberado pelo M1 em 12/10/2026, sem gravar
   CUSIP nem ISIN fora da lista do ADR 0005 (`docs/matriz_de_dados.md`, fonte 6).
3. **O lote do IrRAE ainda não grava resultados:** o `irrae/` calcula em memória, e nada grava a
   média, o P5 e o P95 por empresa. O script de snapshot vai rodar o modelo ou depender de um passo
   novo que grave esses resultados. As ingestões por empresa (10-K, FRE, patentes) também não
   existem em escala.
4. **Faixa da carteira:** a D-01 apresenta os dois cenários de referência (independente e
   comonotônico; `irrae/agregacao.py`). Mostrar só o comonotônico é decisão do M1 (V-09 no ADR 0009).
   A agregação da carteira depende ainda da P-1 (`docs/irrae/especificacao_v1.1.md`).
5. **Caminhos:** a rota é `POST /api/raiox` (ADR 0007). O script fica em `backend/scripts/`, e a
   configuração no backend, e não em `scripts/` e `config/` na raiz.
6. **Contrato:** o tipo do snapshot é gerado de um JSON Schema exportado por um modelo Pydantic do
   backend, como os tipos da API, e não escrito à mão em zod. Os ids seguem o ADR 0005 (`ativo_id` e
   `empresa_id`), e não o ticker puro.
7. **Textos de tela:** entram primeiro em `docs/textos_telas.md` (seção "Vitrine"), em rascunho, e só
   vão para a interface depois de aprovados.
8. **Cobertura americana:** o `big-techs` e o `sp500` precisam da tabela de empresas da SEC (fonte 7),
   que ainda não foi carregada (DT-3). O leitor do N-PORT (`ingest/nport.py`) só foi testado com
   fixture.
9. **BOVA11:** não está na curadoria de ETFs (`cargas/curadoria/fundos_listados.csv`). O CNPJ vem do
   Cadastro de Fundos da CVM, como o texto pede.

---

# Sagital: front-end da vitrine (projeto pessoal, não comercial)

> **Para o Claude Code que vai ler este arquivo.** Ele descreve o site que mostra o raio-x de carteira e o modelo IrRAE como **projeto pessoal de portfólio, sem fins comerciais**. O visitante não informa carteira nenhuma: ele escolhe uma entre **três carteiras prontas** e vê o raio-x dela. Leia o arquivo inteiro antes de começar. Ele não substitui os `CLAUDE.md` do repositório: em caso de conflito, pare e pergunte ao dono (seção 10).

---

## 0. Contexto em poucas linhas

- **O que já existe no repositório** (estado conhecido em out/2026; confira o estado atual antes de começar):
  - `backend/app/`: motor do produto (importação, look-through recursivo, classificação, agregação), com `Decimal` e a API `POST /raiox`.
  - `backend/irrae/` + `backend/ingest/`: o modelo IrRAE (lote, numpy/scipy). Ele roda fora da API e grava, por empresa, média, P5 e P95 (ADR 0004).
  - `frontend/`: React + TypeScript, praticamente vazio (`App.tsx` com 3 linhas).
- **IrRAE v1.1:** carteira → fundos/ETFs (look-through) → ações → exposição fundamental a um tema (hoje, a **Cadeia de IA**), com componentes A, Ir, B, R, N, C, P e prior setorial. Cada empresa tem uma média e uma **faixa estimada** [P5–P95], calculadas por Monte Carlo (S = 2.000 sorteios, semente fixa).
- **Documentos de referência no repositório:** `docs/irrae/relatorio_tecnico_v1.pdf`, `docs/irrae/especificacao_v1.1.md` (se já existir), `docs/adr/0003` e `0004`, `docs/matriz_de_dados.md` e o arquivo de fontes `IrRAE_fontes_de_dados.md` (IDs `FP-xx` / `FA-xx` usados abaixo).

---

## 1. O que muda em relação ao produto original

| Produto original | Vitrine (este documento) |
|---|---|
| O usuário envia a própria carteira (CSV/manual) | **Não existe entrada de carteira.** O visitante escolhe 1 de 3 carteiras fixas |
| API calcula na hora (`POST /raiox`) | **Site estático.** Os resultados são calculados antes, fora do site, e publicados como arquivos JSON ("snapshots") |
| Preocupação com LGPD da carteira do usuário | Não há dado pessoal: as três carteiras são públicas |
| Limites de uso, rate limit por IP, PTAX | Desnecessários no site (não há servidor de cálculo) |
| Produto comercial | **Projeto pessoal, sem fins comerciais.** Nada de preço, plano, cadastro, login, lista de espera ou coleta de e-mail |

**Remover do front (ou não criar):** upload de arquivo, formulário de ativos, campo de ticker, login, qualquer chamada a `POST /raiox`.
**Não apagar do backend:** o código de importação e a API continuam no repositório. Eles só não são usados nem publicados pelo site da vitrine. (Apagar é decisão do dono, seção 10.)

---

## 2. As três carteiras

| ID (usar na URL) | Nome na tela | Composição | Como chega às empresas |
|---|---|---|---|
| `big-techs` | 4 big techs americanas | NVIDIA (NVDA), Amazon (AMZN), Apple (AAPL), Microsoft (MSFT), **25% cada** | Ações diretas, sem look-through |
| `sp500` | S&P 500 | 100% num ETF que replica o índice: **IVV** | Look-through pelas posições do ETF no **N-PORT** da SEC (FP-09/FP-10) |
| `ibovespa` | Ibovespa | 100% num ETF que replica o índice: **BOVA11** | Look-through pela carteira do fundo no **CDA da CVM** (FP-25, arquivos `cda_fie_AAAAMM.csv`) |

**Por que a Microsoft como 4ª empresa:** as quatro formam um degradê didático de exposição à Cadeia de IA. NVIDIA é quase pura (chips), Microsoft e Amazon são parciais pela nuvem (Azure, AWS) e a Apple é majoritariamente hardware de consumo. Isso mostra o modelo diferenciando empresas que o mercado chama todas de "big tech". O dono pode trocar a 4ª empresa; o resto do documento não depende dessa escolha.

**Por que ETFs e não a lista oficial dos índices:**
- A carteira teórica do Ibovespa é dado da B3 e, pelas notas do dono, não será usada na v1 (FP-30). O caminho decidido é o CDA da CVM, com cerca de 1 mês de defasagem.
- Os pesos oficiais do S&P 500 são dado proprietário da S&P Dow Jones Indices. As posições do IVV no N-PORT são públicas na SEC (com cerca de 60 dias de defasagem).
- Na tela, deixar claro: "carteira de um ETF que replica o índice, na data X", e não "a composição oficial do índice".

**Cuidados por carteira:**
- `sp500`: o N-PORT traz CUSIP/ISIN US, sujeitos à licença CGS (FP-18). **Descartar CUSIP e ISIN `US…` na ingestão**; identificar pelas chaves já decididas (LEI, ticker, nome, CIK). A FP-09 ainda está "Pendente" na planilha do dono: confirmar com ele antes de baixar (seção 10).
- `ibovespa`: posições confidenciais do CDA (`cda_fie_CONFID_*`) entram como **"não coberto"**. Achar o CNPJ do BOVA11 no Cadastro de Fundos da CVM (FP-26); não digitar de memória. ISIN `BR…` pode ser armazenado.
- `sp500` e `ibovespa` têm centenas de empresas, e o IrRAE completo pode não estar calculado para todas. Regra padrão (o dono pode mudar): calcular o IrRAE para as maiores posições até cobrir a maior fração possível do peso; o resto entra como "não coberto" ou com classificação só pelo prior setorial (selo "preliminar"). **A tela sempre mostra a cobertura** ("IrRAE calculado para X% do peso da carteira").

---

## 3. Arquitetura

```
backend/ (lote)                                   frontend/ (site estático)
scripts/gerar_snapshots_vitrine.py  ──►  frontend/public/snapshots/{big-techs,sp500,ibovespa}.json
  usa app/core (look-through, Decimal)              ▲
  usa irrae/ (IrRAE por empresa)                    │ fetch no navegador
                                                  Vite build → hospedagem estática
```

1. **Script de snapshot** (`scripts/gerar_snapshots_vitrine.py`): recebe a definição das 3 carteiras (`config/vitrine_carteiras.json`), faz o look-through com `app/core/lookthrough.py` (uma implementação só; ver decisão X-03), lê o IrRAE já calculado pelo lote e grava um JSON por carteira no formato da seção 4. Os caminhos de dados reais vêm por parâmetro, como nos demais scripts.
2. **Front** (`frontend/`): React + TypeScript + Vite. Confira o `package.json` existente e mantenha o que já está lá. Gráficos em SVG próprio ou numa biblioteca leve; nada de dependência pesada só para um gráfico.
3. **Sem servidor de cálculo** em produção. O site é só HTML, JS e os 3 JSON.
4. **Rotas:** `/` (escolha da carteira), `/carteira/:id`, `/carteira/:id/empresa/:empresaId`, `/metodologia`, `/fontes`. A carteira escolhida fica na URL, para o link poder ser compartilhado.
5. **Enquanto não houver snapshot com dados reais:** usar `frontend/src/dados_exemplo/*.json` com **dados sintéticos**, no mesmo formato, e mostrar uma faixa fixa no topo: "Dados ilustrativos: ainda não calculados com dados reais". **Nunca inventar números "realistas"** para NVDA, AAPL etc., nem copiar os do relatório técnico como se fossem atuais.

---

## 4. Formato do snapshot (contrato entre o lote e o front)

Validar com um schema (por exemplo, zod) no carregamento; se o arquivo não bater, mostrar erro claro em vez de tela quebrada.

```json
{
  "versao_schema": "1",
  "carteira": {
    "id": "big-techs",
    "nome": "4 big techs americanas",
    "descricao": "NVIDIA, Amazon, Apple e Microsoft, 25% cada.",
    "data_referencia": "AAAA-MM-DD",
    "posicoes": [
      { "id": "NVDA", "nome": "NVIDIA", "tipo": "acao", "peso": 0.25 }
    ]
  },
  "modelo": {
    "versao_irrae": "1.1",
    "n_amostras": 2000,
    "semente": 0,
    "gerado_em": "AAAA-MM-DDThh:mm:ssZ",
    "cenario_faixa_carteira": "comonotonico"
  },
  "cobertura": { "peso_com_irrae": 0.0, "peso_so_prior": 0.0, "peso_nao_coberto": 0.0 },
  "exposicao": {
    "setores": [ { "id": "", "nome": "", "peso": 0.0 } ],
    "temas": [
      {
        "id": "cadeia_ia", "nome": "Cadeia de IA",
        "media": 0.0, "p5": 0.0, "p95": 0.0,
        "subtemas": [ { "id": "", "nome": "", "media": 0.0, "p5": 0.0, "p95": 0.0 } ]
      }
    ],
    "fora_do_tema": 0.0,
    "nao_coberto": 0.0
  },
  "empresas": [
    {
      "empresa_id": "", "ticker": "", "nome": "", "pais": "US",
      "peso_efetivo": 0.0,
      "caminho": ["IVV"],
      "setor": "",
      "irrae": {
        "origem": "irrae | so_prior | nao_coberto",
        "tema": "cadeia_ia", "media": 0.0, "p5": 0.0, "p95": 0.0,
        "selo": "alta | media | preliminar",
        "folhas": [ { "id": "", "nome": "", "media": 0.0, "p5": 0.0, "p95": 0.0 } ],
        "componentes": [ { "id": "A", "nome": "Atividade", "peso_p": 0.0, "presente": true } ]
      },
      "fontes": [ { "id": "FP-03", "descricao": "", "url": "", "data": "AAAA-MM-DD" } ]
    }
  ],
  "fontes_carteira": [ { "id": "FP-25", "descricao": "", "url": "", "data_referencia": "AAAA-MM-DD" } ]
}
```

Notas do contrato:
- **Taxonomia (temas, subtemas, folhas) e limiares do selo** vêm da configuração do `irrae/` (`config/` e `regras.py`), não de valores digitados no front.
- `peso_efetivo` é o peso da empresa depois do look-through, somando caminhos diretos e via ETF (classes da mesma empresa consolidadas, por exemplo GOOGL/GOOG pelo CIK).
- **P5 e P95 do tema e de cada subtema precisam ser gravados pelo lote**, porque os quantis das folhas não somam para dar o quantil do tema (lacuna (1) da decisão X-02).
- Todos os pesos de uma carteira fecham 100%: soma dos temas + fora do tema + não coberto = 1. O script de snapshot verifica isso e falha se não fechar (tolerância de ponto flutuante).
- Nenhum campo com CUSIP ou ISIN `US…`/`CA…`.

---

## 5. Telas

### 5.1 Início (`/`)
- Uma frase sobre o que é: "Raio-x de carteira: quanto do seu dinheiro depende, de verdade, da cadeia de IA."
- Aviso curto e visível: **projeto pessoal, sem fins comerciais, não é recomendação de investimento.**
- **Três cartões, um por carteira**, com nome, uma linha de descrição e a data de referência. Clicar abre o raio-x.
- Um bloco de 3 passos mostrando as camadas: carteira → fundos → empresas → exposição.

### 5.2 Raio-x da carteira (`/carteira/:id`)
1. **Seletor das 3 carteiras** sempre visível no topo (abas ou segmentado), para trocar sem voltar ao início.
2. **Número principal:** exposição à Cadeia de IA, no formato `34% [28–41]`, com o rótulo "faixa estimada" e um ícone de ajuda (seção 6).
3. **Duas visões que fecham 100%:**
   - **Por setor:** a empresa inteira vai para um setor.
   - **Por tema:** cada empresa é repartida (ex.: parte da Amazon vai para "Nuvem e plataformas", o resto para "Fora da cadeia de IA").
   - Explicar numa linha por que as duas visões dão números diferentes.
4. **Subtemas** da Cadeia de IA, com média e faixa.
5. **Cobertura e "não coberto"** sempre à mostra, nunca escondidos num rodapé.
6. **Tabela de empresas:** ticker, nome, peso efetivo, IrRAE (média e faixa), selo e **contribuição para o tema** (peso × média). Ordenável; nas carteiras grandes, paginar ou mostrar as 20 maiores com "ver todas".
7. **Look-through** (só `sp500` e `ibovespa`): ETF → empresas, mostrando que 100% do ETF virou N empresas.
8. **Datas:** data de referência da carteira (N-PORT ou CDA) e data de geração do snapshot.

### 5.3 Empresa (`/carteira/:id/empresa/:empresaId`)
- IrRAE da empresa com faixa e selo.
- Folhas/subtemas da empresa.
- **Componentes:** quais fontes entraram (A, Ir, B, R, N, C, P, prior), o peso p de cada uma e quais faltaram (os pesos se redistribuem entre as presentes).
- **Fontes com link** para o documento original (ex.: o 10-K na SEC, o FRE na CVM) e a data.
- Para empresas `so_prior` ou `nao_coberto`: explicar o porquê, sem mostrar faixa inventada.

### 5.4 Metodologia (`/metodologia`)
Texto curto e didático, sem fórmulas no topo e com detalhes expansíveis:
1. Por que o resultado é uma faixa, e não um número só.
2. Sorteios (Monte Carlo) e o que são P5 e P95.
3. Dirichlet em uma frase: "mais evidência, faixa mais estreita".
4. Como a carteira junta as empresas e qual hipótese a faixa da carteira usa.
5. O que o modelo **não** faz (não prevê preço, não recomenda compra ou venda).
6. Link para o relatório técnico em PDF e referências (Gelman et al., *Bayesian Data Analysis*, 3ª ed., 2013, seção 3.4; Robert e Casella, *Monte Carlo Statistical Methods*, 2ª ed., 2004; Bates e Granger, 1969).

### 5.5 Fontes e licenças (`/fontes`)
Lista completa da seção 8, com links.

---

## 6. Regras de apresentação dos números

- **Formato brasileiro:** vírgula decimal, `%` colado ao número, faixa entre colchetes com travessão curto: `69% [56–81]`. Arredondar para inteiro na visão geral e uma casa decimal nas tabelas de peso.
- **Nunca usar "IC90", "intervalo de confiança" ou "90% de confiança".** O termo é **"faixa estimada"**.
- **Faixa da carteira:** o snapshot só traz o cenário de erros alinhados (comonotônico; soma dos quantis ponderados). Rótulo obrigatório no ícone de ajuda: "Faixa estimada, supondo que os erros das empresas andam juntos." **Não chamar de "conservadora"** nem dizer que "a verdade fica entre os dois cenários".
- **Selo** (alta / média / preliminar) pela largura P95 − P5, com os limiares lidos da configuração do modelo. Mostrar a regra no ícone de ajuda.
- **Sem verbos de recomendação:** nada de "compre", "venda", "reduza", "aumente", "ideal", "melhor carteira". O site mostra exposição e concentração. Recomendação de investimento exige registro na CVM (Resolução CVM 19/2021).
- **Comparação entre as 3 carteiras:** permitida (é o ponto alto da vitrine), mas descritiva: "a carteira X tem mais exposição à Cadeia de IA que a Y", sem juízo de valor.

---

## 7. Identidade visual

Sugestão levantada nas conversas sobre a marca (não é decisão fechada; o dono pode ajustar):
- **Base escura de exame de imagem:** azul-marinho quase preto; linhas e destaques em **ciano luminoso**.
- **Um único acento quente** (âmbar ou coral), usado só onde algo importa: o número principal e a área que mais contribui para o tema.
- **Conceito "camadas"** (cortes de ressonância em sequência) para a animação da carteira se abrindo em fundos e empresas.
- Evitar roxo, laranja e preto com amarelo (associados a bancos e corretoras brasileiros).
- **Sem logos** de empresas, índices, bolsas ou órgãos (SEC, EDGAR, CVM, B3, USPTO, INPI, GLEIF). Usar só nomes e tickers em texto.
- Acessibilidade: contraste AA, nada transmitido só por cor (a faixa também aparece em texto), navegação por teclado, layout responsivo (celular primeiro).
- Tema escuro como padrão; tema claro opcional.

---

## 8. Fontes, atribuições e avisos

**Rodapé de todas as páginas:**
> Projeto pessoal, sem fins comerciais. Não é recomendação de investimento. Sem vínculo com a SEC, a CVM, a B3, a S&P Dow Jones Indices, os gestores dos ETFs ou as empresas citadas. Nomes de índices, fundos e empresas pertencem aos seus titulares e aparecem só para identificar as carteiras.

**Atribuições na página `/fontes`** (só as das fontes realmente usadas no snapshot; o script grava a lista em `fontes_carteira` e `fontes`):

| Fonte | O que exibir / respeitar | Ref. |
|---|---|---|
| SEC (EDGAR, APIs, FSN, N-PORT) | Citar a SEC e a empresa como fonte. Não usar "SEC", o logo do EDGAR nem sugerir vínculo | FP-01 a FP-10 |
| CVM Dados Abertos (DFP, ITR, FRE, CDA, cadastros) | "Fonte: CVM, Dados Abertos (licença ODbL)", com link para a licença | FP-21 a FP-26 |
| USPTO (AIPD, Patent Assignment) | Crédito à USPTO; citar a documentação do dataset (AIPD; Marco et al., 2015); sem logo | FP-12, FP-15 |
| PatentsView | CC BY 4.0: criador, link da licença, link da fonte e aviso de que os dados foram modificados | FP-14 |
| OpenAlex | "Fonte: OpenAlex" (CC0, por boa prática) | FA-04 |
| IBGE / CONCLA | "Fonte: IBGE/CONCLA, CNAE 2.3" (confirmar a versão vigente) | FP-35 |
| Receita Federal | "Fonte: Receita Federal, Dados Abertos do CNPJ" | FP-34 |
| BCB (se aparecer câmbio) | Repassar o aviso de responsabilidade da API Olinda | FP-36 |
| Census (só se a API for usada) | Aviso exigido: "This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau." | FP-20 |

**Atenção à ODbL no snapshot `ibovespa`:** o JSON é baixado pelo navegador, então ele é uma base derivada de dados da CVM publicada abertamente. Pela ODbL, base derivada publicada deve sair sob a mesma licença (share-alike). Proposta: declarar no próprio JSON e na página `/fontes` que os dados derivados da CVM estão sob ODbL. Confirmar com o dono (seção 10).

---

## 9. O que não fazer

1. Não criar nenhuma forma de o visitante enviar carteira, ticker ou arquivo.
2. Não chamar APIs externas (SEC, CVM, cotações) **a partir do navegador**. Todo dado vem dos snapshots.
3. Não usar cotações nem preços: o IrRAE v1.1 roda sem preços, e as carteiras são definidas por peso.
4. Não usar Yahoo Finance, dados de índice da B3, GICS ou classificação ANBIMA.
5. Não armazenar nem exibir CUSIP ou ISIN `US…`/`CA…`.
6. Não exibir os campos `label`/`description` da API `companyfacts` (textos da taxonomia FASB). Usar rótulos próprios em português.
7. Não incluir analytics, cookies de rastreamento ou scripts de terceiros (regra do `frontend/CLAUDE.md`).
8. Não inventar números de IrRAE nem copiar os do relatório como atuais (seção 3, item 5).
9. Não mudar `irrae/` nem `app/core/` para "fazer a tela funcionar". Se o snapshot precisar de algo que o lote não grava, abrir uma issue e perguntar.

---

## 10. Decisões que o agente não toma (perguntar ao dono)

| # | Decisão | Proposta padrão |
|---|---|---|
| V-01 | Commitar os snapshots com dados reais no repositório. A regra atual diz "só dados sintéticos em código, testes, logs" | Exceção documentada no `CLAUDE.md`: snapshots públicos das 3 carteiras podem ir para `frontend/public/snapshots/` (não contêm dado pessoal); o resto continua fora |
| V-02 | Liberar o N-PORT (FP-09, ainda "Pendente") para a carteira `sp500` | Usar, descartando CUSIP/ISIN US na ingestão |
| V-03 | Licença dos snapshots derivados da CVM (ODbL share-alike) | Declarar ODbL no JSON e em `/fontes` |
| V-04 | Corte de cobertura do IrRAE em `sp500` e `ibovespa` | Maiores posições até a maior cobertura possível; resto "não coberto" ou "só prior" |
| V-05 | Apagar ou manter o código de importação de carteira e o `POST /raiox` | Manter no backend; só não publicar |
| V-06 | Repositório público ou privado | Manter o repositório privado e publicar só o site gerado |
| V-07 | Hospedagem e domínio | Hospedagem estática gratuita; domínio a definir |
| V-08 | Autoria e contato no site | Preencher: nome do autor e link (GitHub/LinkedIn). Sem formulário de contato |

---

## 11. Ordem de trabalho sugerida (PRs pequenos)

1. **PR 1, esqueleto:** rotas, layout, tema visual, rodapé com avisos, página `/fontes` e `/metodologia` com texto provisório.
2. **PR 2, contrato:** schema do snapshot, `dados_exemplo/*.json` sintéticos para as 3 carteiras, carregamento e validação, faixa "Dados ilustrativos".
3. **PR 3, raio-x da carteira:** número principal, setor × tema, subtemas, cobertura, tabela de empresas, seletor de carteiras.
4. **PR 4, empresa e look-through.**
5. **PR 5, script de snapshot** (`scripts/gerar_snapshots_vitrine.py` + `config/vitrine_carteiras.json`), com testes em dados sintéticos. Rodar com dados reais só depois de V-01 a V-04.
6. **PR 6, build e deploy estático.**

---

## 12. Critérios de aceite

- [ ] Não existe nenhum campo, botão ou rota que aceite carteira do visitante.
- [ ] As 3 carteiras abrem, trocam pelo seletor e têm URL própria.
- [ ] Em cada carteira, temas + fora do tema + não coberto = 100% (teste automático no script e no front).
- [ ] Toda faixa aparece como "faixa estimada", nunca como "IC" ou "confiança".
- [ ] Cobertura e "não coberto" visíveis na tela principal.
- [ ] Data de referência e data de geração visíveis.
- [ ] Rodapé com os avisos da seção 8 em todas as páginas; `/fontes` com as atribuições das fontes usadas.
- [ ] Nenhum logo de terceiros, nenhum CUSIP/ISIN US, nenhuma chamada externa no navegador, nenhum analytics.
- [ ] Com dados de exemplo, a faixa "Dados ilustrativos" aparece em todas as telas.
- [ ] Funciona no celular, navegação por teclado, contraste AA.
- [ ] `npm run build` gera um site estático que abre sem backend.
