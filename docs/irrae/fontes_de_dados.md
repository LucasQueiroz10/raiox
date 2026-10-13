# IrRAE — Fontes de dados (transcrição integral do Excel para o Claude Code)

> **Fonte:** planilha de fontes de dados do M1 (`Fontes_de_dados_IrRAE.xlsx`), versão modificada em
> 10/10/2026, conferida célula a célula contra a planilha original em 12/10/2026. As fórmulas da
> planilha são só contagens da aba `Leia-me`, transcritas como texto na Seção 1; nenhuma entra na
> metodologia.

> **Para o Claude Code que vai ler este arquivo.** Este documento é a transcrição *integral e literal* da planilha `Fontes_de_dados_IrRAE.xlsx` (4 abas), feita por script e conferida célula a célula. Nenhum texto do Excel foi resumido, corrigido ou reescrito. Tudo o que **não** veio do Excel está isolado nas seções marcadas **[REVISOR]** (Seções 0, 5, 6 e 7) e nas linhas iniciadas por '> Nota do revisor', e nunca dentro das fichas de fonte.

## Seção 0 — [REVISOR] Como ler este arquivo

1. **Estrutura.** Seção 1 = aba `Leia-me`. Seção 2 = aba `Fontes principais` (38 fichas, IDs `FP-01`…`FP-37` e `FP-15b`). Seção 3 = aba `Fontes adicionais` (10 fichas, IDs `FA-01`…`FA-10`). Seção 4 = aba `Base legal` (15 normas, IDs `BL-01`…`BL-15`). Seção 5 = decisões de uso resumidas (interpretação do revisor). Seção 6 = inconsistências e ambiguidades encontradas no Excel. Seção 7 = como a integridade foi verificada.
2. **IDs.** Os IDs `FP-xx`, `FA-xx` e `BL-xx` foram criados nesta transcrição para referência inequívoca (seguem a coluna `#` do Excel). A única linha sem número no Excel (linha 18 de `Fontes principais`) recebeu o ID `FP-15b` — ver Seção 6, item 1.
3. **Campos.** Cada ficha lista *todas* as colunas da aba, com o nome exato do cabeçalho, a letra da coluna e a célula de origem. `∅ (célula vazia)` = célula sem conteúdo no Excel. Textos com quebra de linha aparecem dentro de blocos ```text``` exatamente como no Excel (tabulações e linhas em branco preservadas). Quando a célula tinha espaços/quebras sobrando no início ou no fim, isso é registrado na linha ⚠️ logo abaixo. Hiperlinks embutidos nas células (que podem diferir do texto visível) aparecem na linha 🔗.
4. **Hierarquia entre colunas (regra para decidir conflitos dentro de uma mesma ficha).** Pela própria aba `Leia-me` (B3 e B7): `Status preliminar` e `Validade jurídica (leitura preliminar — confirmar)` são uma leitura preliminar feita em 29/09/2026; `Sua verificação` e `Notas da sua pesquisa` foram preenchidas depois pelo dono do projeto. **Portanto, quando houver conflito, vale: `Notas da sua pesquisa` > `Observações` > `Validade jurídica` > `Status preliminar`.** O `Status preliminar` NÃO foi atualizado depois das notas (ex.: INPI continua 'A verificar' embora as notas já concluam o uso).
5. **Significado de `VALIDADO` na coluna `Sua verificação`.** O valor `VALIDADO` não pertence à lista de validação da planilha (`Pendente, Aprovado, Aprovado com condições, Reprovado`). Leitura do revisor: `VALIDADO` = *o dono concluiu a pesquisa sobre a fonte*; **NÃO significa 'liberado para uso'**. Prova: `FP-18` (CUSIP) está `VALIDADO` e a nota diz 'NAO USAR'. A decisão de uso de cada fonte está nas `Notas da sua pesquisa`, resumida na Seção 5.
6. **Termos do projeto.** IrRAE = o modelo (v1.1: carteira → ações → exposição fundamental). 'Sagital' aparece em algumas notas: é o nome do app/projeto que usa o IrRAE. As siglas dos componentes (A, Ir, B, R, N, C, P, Prior, Look-through, Auditoria) estão definidas na Seção 1 (célula B5). Referências como 'ref. [2]', 'seção 5.10' e 'relatório v1' apontam para um relatório do IrRAE que **não está incluído neste arquivo**.
7. **Isto não é parecer jurídico.** Ver aviso na Seção 1 (célula B3).

## Seção 1 — Aba `Leia-me` (transcrição integral)

Título (célula A1): **Fontes de dados do IrRAE**

- **Objetivo** (célula A2): Lista das bases que alimentam o IrRAE v1.1 (carteira → ações → exposição fundamental), com jurisdição, onde obter, leitura preliminar dos termos de uso e observações. Serve de checklist para a sua verificação jurídica, fonte por fonte.
- **Aviso** (célula A3): A coluna 'Validade jurídica' é uma leitura preliminar dos termos públicos, feita em 29/09/2026. Não é parecer jurídico. Confirme cada item (idealmente com advogado) antes de uso comercial ou de oferecer API a terceiros.
- **Abas** (célula A4): 'Fontes principais': bases usadas ou previstas no modelo (EUA e Brasil).  'Fontes adicionais': bases confiáveis extras, com a finalidade de cada uma.  'Base legal': normas e licenças citadas.
- **Componentes (siglas)** (célula A5): A = Atividade (receita e lucro por segmento) · Ir = Investimento (capex) · B = Backlog/carteira contratada · R = Patentes · N = Narrativa (texto) · C = Cadeia de clientes · P = Participações/aquisições · Prior = prior setorial · Look-through = abrir ETFs/fundos da carteira · Auditoria = calibração por retornos (não entra na exposição na v1.1).
- **Status preliminar** (célula A6): Livre = licença aberta sem condições relevantes · Livre com condições = uso permitido respeitando regras (atribuição, limite de requisições, share-alike etc.) · Licença/contrato necessário = uso comercial exige contrato ou autorização · A verificar = termos não encontrados ou ambíguos.
- **O que você preenche** (célula A7): Colunas amarelas 'Sua verificação' (lista: Pendente / Aprovado / Aprovado com condições / Reprovado) e 'Notas da sua pesquisa'. Exemplo: 'Aprovado com condições' + 'Termos lidos em 30/09/2026; exige atribuição e 10 req/s'.
- **Componente E removido** (célula A8): Na v1.1 o Enquadramento via ETFs foi retirado; o N-PORT e o CDA ficam só para abrir ETFs/fundos que estiverem na carteira, sem classificar ETFs por tema.
- (linha 9 vazia no Excel)
- **Resumo** (célula A10) — título de bloco, sem valor em B10
- **Total de fontes principais** (célula A11) → valor calculado no Excel: **38** · fórmula em B11: `=COUNTA('Fontes principais'!B3:B40)`
- **EUA** (célula A12) ⚠️ rótulo com espaços no início no Excel: "  EUA" (indentação visual = subitem) → valor calculado no Excel: **19** · fórmula em B12: `=COUNTIF('Fontes principais'!D3:D40,"EUA")`
- **Brasil** (célula A13) ⚠️ rótulo com espaços no início no Excel: "  Brasil" (indentação visual = subitem) → valor calculado no Excel: **17** · fórmula em B13: `=COUNTIF('Fontes principais'!D3:D40,"Brasil")`
- **Internacional** (célula A14) ⚠️ rótulo com espaços no início no Excel: "  Internacional" (indentação visual = subitem) → valor calculado no Excel: **2** · fórmula em B14: `=COUNTIF('Fontes principais'!D3:D40,"Internacional*")`
- **Status: Livre** (célula A15) → valor calculado no Excel: **0** · fórmula em B15: `=COUNTIF('Fontes principais'!J3:J40,"Livre")`
- **Status: Livre com condições** (célula A16) → valor calculado no Excel: **25** · fórmula em B16: `=COUNTIF('Fontes principais'!J3:J40,"Livre com condições")`
- **Status: Licença/contrato necessário** (célula A17) → valor calculado no Excel: **5** · fórmula em B17: `=COUNTIF('Fontes principais'!J3:J40,"Licença/contrato necessário")`
- **Status: A verificar** (célula A18) → valor calculado no Excel: **8** · fórmula em B18: `=COUNTIF('Fontes principais'!J3:J40,"A verificar")`
- **Sua verificação: concluídas** (célula A19) → valor calculado no Excel: **36** · fórmula em B19: `=COUNTA('Fontes principais'!N3:N40)-COUNTIF('Fontes principais'!N3:N40,"Pendente")`
- **Fontes adicionais** (célula A20) → valor calculado no Excel: **10** · fórmula em B20: `=COUNTA('Fontes adicionais'!B3:B12)`

> Nota do revisor: as contagens acima usam a coluna `Status preliminar` (leitura de 29/09/2026), não as notas posteriores do dono. 'Sua verificação: concluídas' = 36 porque 36 das 38 linhas estão diferentes de 'Pendente' (FP-09 e FP-10 estão 'Pendente').

## Seção 2 — Aba `Fontes principais` (38 fichas, transcrição integral)

Título da aba (célula A1): **Fontes principais do IrRAE v1.1 — EUA, Internacional e Brasil**

Colunas da aba, na ordem do Excel: A = `#` · B = `Sigla / Nome da base` · C = `Órgão / mantenedor` · D = `Jurisdição` · E = `Componente IrRAE` · F = `O que fornece` · G = `Link / onde encontrar` · H = `Tipo de acesso` · I = `Custo` · J = `Status preliminar` · K = `Validade jurídica (leitura preliminar — confirmar)` · L = `Link dos termos de uso` · M = `Observações` · N = `Sua verificação` · O = `Notas da sua pesquisa`

Lista suspensa definida no Excel para N3:N40: "Pendente,Aprovado,Aprovado com condições,Reprovado" (valores não listados, como `VALIDADO`, foram digitados manualmente).

### FP-01 · SEC EDGAR – Arquivo de documentos (Archives)

- Origem: aba `Fontes principais`, linha 3 do Excel.
- **#** (coluna A, célula A3): 1
- **Sigla / Nome da base** (coluna B, célula B3): SEC EDGAR – Arquivo de documentos (Archives)
- **Órgão / mantenedor** (coluna C, célula C3): U.S. SEC
- **Jurisdição** (coluna D, célula D3): EUA
- **Componente IrRAE** (coluna E, célula E3): A, Ir, B, N, C, P
- **O que fornece** (coluna F, célula F3): Todos os filings: 10-K, 10-Q, 8-K (Exhibit 99.1 = releases), Exhibit 21 (lista de subsidiárias), Schedule 13D/13G (participações ≥5%), 8-K Item 2.01 (aquisições).
- **Link / onde encontrar** (coluna G, célula G3): https://www.sec.gov/edgar/search/  |  arquivos: https://www.sec.gov/Archives/edgar/data/
- **Tipo de acesso** (coluna H, célula H3): Web + HTTP (sem chave); índices diários/completos para lote
- **Custo** (coluna I, célula I3): Gratuito
- **Status preliminar** (coluna J, célula J3): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K3): Política da SEC: "Information presented on sec.gov is considered public information and may be copied or further distributed by users of the web site without the SEC's permission." Restrições: não usar logos/marcas SEC/EDGAR; acesso automatizado limitado a 10 req/s com User-Agent declarado (nome + e-mail).
- **Link dos termos de uso** (coluna L, célula L3): https://www.sec.gov/about/privacy-information  |  https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- **Observações** (coluna M, célula M3): Fonte principal do protótipo v1. Exhibit 21 ajuda a ligar subsidiárias à controladora (patentes, participações). Texto do 10-K é redigido pela empresa: citar a SEC/empresa como fonte.
- **Sua verificação** (coluna N, célula N3): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O3):
```text
If a user or application submits more than 10 requests per second, further requests from the IP address(es) may be limited for a brief period.   

Não pode usar "SEC", o logo do EDGAR ou nomes parecidos no seu produto ou marketing sem licença, nem dar a entender que tem vínculo com a SEC.
```

### FP-02 · SEC EDGAR APIs (data.sec.gov)

- Origem: aba `Fontes principais`, linha 4 do Excel.
- **#** (coluna A, célula A4): 2
- **Sigla / Nome da base** (coluna B, célula B4): SEC EDGAR APIs (data.sec.gov)
- **Órgão / mantenedor** (coluna C, célula C4): U.S. SEC
- **Jurisdição** (coluna D, célula D4): EUA
- **Componente IrRAE** (coluna E, célula E4): A (totais), Ir, B, cadastro
- **O que fornece** (coluna F, célula F4): submissions (histórico de filings), companyfacts, companyconcept e frames (XBRL). Tags úteis: PaymentsToAcquirePropertyPlantAndEquipment (capex), RevenueRemainingPerformanceObligation (backlog/RPO).
- **Link / onde encontrar** (coluna G, célula G4): https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- **Tipo de acesso** (coluna H, célula H4): API REST JSON, sem chave; bulk companyfacts.zip e submissions.zip (atualização noturna)
- **Custo** (coluna I, célula I4): Gratuito
- **Status preliminar** (coluna J, célula J4): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K4): Mesma política da SEC acima. Acesso automatizado deve seguir a Privacy and Security Policy e o limite de 10 req/s.
- **Link dos termos de uso** (coluna L, célula L4): https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- **Observações** (coluna M, célula M4): Não traz dados por segmento (dimensões XBRL ficam de fora) — para segmentos use FSN ou o XBRL do filing.
- **Sua verificação** (coluna N, célula N4): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O4):
```text
Currently included in the APIs are the submissions history by filer and the XBRL data from financial statements (forms 10-Q, 10-K,8-K, 20-F, 40-F, 6-K, and their variants).
The JSON structures are updated throughout the day, in real time, as submissions are disseminated.
In addition, a bulk ZIP file is available to download all the JSON structures for an API. This ZIP file is updated and republished nightly at approximately 3:00 a.m. ET.
```

### FP-03 · SEC Financial Statement and Notes Data Sets (FSN)

- Origem: aba `Fontes principais`, linha 5 do Excel.
- **#** (coluna A, célula A5): 3
- **Sigla / Nome da base** (coluna B, célula B5): SEC Financial Statement and Notes Data Sets (FSN)
- **Órgão / mantenedor** (coluna C, célula C5): U.S. SEC (DERA)
- **Jurisdição** (coluna D, célula D5): EUA
- **Componente IrRAE** (coluna E, célula E5): A (receita e lucro por segmento), C (clientes ≥10%)
- **O que fornece** (coluna F, célula F5): Todos os fatos XBRL das demonstrações e notas, incluindo dimensões (ex.: StatementBusinessSegmentsAxis, concentração de clientes).
- **Link / onde encontrar** (coluna G, célula G5): https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets
- **Tipo de acesso** (coluna H, célula H5): Download em lote (zip mensal/trimestral)
- **Custo** (coluna I, célula I5): Gratuito
- **Status preliminar** (coluna J, célula J5): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K5): Mesma política da SEC. Dados derivados de filings públicos.
- **Link dos termos de uso** (coluna L, célula L5): https://www.sec.gov/about/privacy-information
  - 🔗 Hiperlink embutido na célula (alvo exato): `https://www.sec.gov/about/privacy-information`
- **Observações** (coluna M, célula M5): Melhor caminho para segmentos em lote. Previsto no código v1, ainda não executado com dados reais.
- **Sua verificação** (coluna N, célula N5): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O5): ∅ (célula vazia)

### FP-04 · SEC Financial Statement Data Sets

- Origem: aba `Fontes principais`, linha 6 do Excel.
- **#** (coluna A, célula A6): 4
- **Sigla / Nome da base** (coluna B, célula B6): SEC Financial Statement Data Sets
- **Órgão / mantenedor** (coluna C, célula C6): U.S. SEC (DERA)
- **Jurisdição** (coluna D, célula D6): EUA
- **Componente IrRAE** (coluna E, célula E6): A (totais)
- **O que fornece** (coluna F, célula F6): Versão simplificada (só demonstrações principais, sem notas).
- **Link / onde encontrar** (coluna G, célula G6): Onde achar: sec.gov → Data & Research → Financial Statement Data Sets
- **Tipo de acesso** (coluna H, célula H6): Download em lote (zip trimestral)
- **Custo** (coluna I, célula I6): Gratuito
- **Status preliminar** (coluna J, célula J6): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K6): Mesma política da SEC.
- **Link dos termos de uso** (coluna L, célula L6): https://www.sec.gov/about/privacy-information
- **Observações** (coluna M, célula M6): Alternativa leve ao FSN quando não precisar de segmentos.
- **Sua verificação** (coluna N, célula N6): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O6): ∅ (célula vazia)

### FP-05 · XBRL / Inline XBRL de cada filing (R-files)

- Origem: aba `Fontes principais`, linha 7 do Excel.
- **#** (coluna A, célula A7): 5
- **Sigla / Nome da base** (coluna B, célula B7): XBRL / Inline XBRL de cada filing (R-files)
- **Órgão / mantenedor** (coluna C, célula C7): U.S. SEC / empresas
- **Jurisdição** (coluna D, célula D7): EUA
- **Componente IrRAE** (coluna E, célula E7): A, Ir, B
- **O que fornece** (coluna F, célula F7): Instância XBRL do 10-K/10-Q e páginas R (ex.: R32.htm = nota de segmentos).
- **Link / onde encontrar** (coluna G, célula G7): Dentro de cada filing em https://www.sec.gov/Archives/edgar/data/<CIK>/
- **Tipo de acesso** (coluna H, célula H7): HTTP (sem chave)
- **Custo** (coluna I, célula I7): Gratuito
- **Status preliminar** (coluna J, célula J7): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K7): Mesma política da SEC.
- **Link dos termos de uso** (coluna L, célula L7): https://www.sec.gov/about/privacy-information
- **Observações** (coluna M, célula M7): Usado nas refs. [2] e [3] do relatório. Conferir soma dos segmentos contra o consolidado (caso Alphabet).
- **Sua verificação** (coluna N, célula N7): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O7): ∅ (célula vazia)

### FP-06 · EDGAR Full-Text Search (EFTS)

- Origem: aba `Fontes principais`, linha 8 do Excel.
- **#** (coluna A, célula A8): 6
- **Sigla / Nome da base** (coluna B, célula B8): EDGAR Full-Text Search (EFTS)
- **Órgão / mantenedor** (coluna C, célula C8): U.S. SEC
- **Jurisdição** (coluna D, célula D8): EUA
- **Componente IrRAE** (coluna E, célula E8): N (narrativa), exposição negativa
- **O que fornece** (coluna F, célula F8): Busca por palavra/frase dentro de filings desde 2001.
- **Link / onde encontrar** (coluna G, célula G8): Interface: https://www.sec.gov/edgar/search/  |  endpoint JSON: https://efts.sec.gov/LATEST/search-index?q=
- **Tipo de acesso** (coluna H, célula H8): Web; endpoint JSON usado pela própria página (sem chave)
- **Custo** (coluna I, célula I8): Gratuito
- **Status preliminar** (coluna J, célula J8): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K8): Mesma política da SEC, mas o endpoint JSON não é documentado oficialmente como API: pode mudar sem aviso.
- **Link dos termos de uso** (coluna L, célula L8): https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
  - 🔗 Hiperlink embutido na célula (alvo exato): `https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`
- **Observações** (coluna M, célula M8): Para N em escala, o mais robusto é baixar o 10-K e contar frases localmente; o EFTS serve para triagem.
- **Sua verificação** (coluna N, célula N8): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O8):
```text
Livre com identificacao de user agent

import time, requests

HEADERS = {
    "User-Agent": "MinhaEmpresa Ltda contato@minhaempresa.com.br",
    "Accept-Encoding": "gzip, deflate",
}

def get_json(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    time.sleep(0.12)  # ~8 req/s, margem abaixo do limite de 10
    return r.json()

dados = get_json("https://data.sec.gov/submissions/CIK0000320193.json")
```

### FP-07 · SEC company_tickers.json

- Origem: aba `Fontes principais`, linha 9 do Excel.
- **#** (coluna A, célula A9): 7
- **Sigla / Nome da base** (coluna B, célula B9): SEC company_tickers.json
- **Órgão / mantenedor** (coluna C, célula C9): U.S. SEC
- **Jurisdição** (coluna D, célula D9): EUA
- **Componente IrRAE** (coluna E, célula E9): Cadastro / look-through
- **O que fornece** (coluna F, célula F9): Mapa ticker ↔ CIK ↔ nome da empresa.
- **Link / onde encontrar** (coluna G, célula G9): https://www.sec.gov/files/company_tickers.json
- **Tipo de acesso** (coluna H, célula H9): Arquivo JSON (sem chave)
- **Custo** (coluna I, célula I9): Gratuito
- **Status preliminar** (coluna J, célula J9): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K9): Mesma política da SEC.
- **Link dos termos de uso** (coluna L, célula L9): https://www.sec.gov/about/privacy-information
- **Observações** (coluna M, célula M9): Consolidar classes da mesma empresa (GOOGL/GOOG) pelo CIK.
- **Sua verificação** (coluna N, célula N9): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O9): O próprio Webmaster FAQ diz que a SEC atualiza esse arquivo periodicamente e não garante que esteja correto ou completo (https://www.sec.gov/about/webmaster-frequently-asked-questions#ticker-cik). Vale colocar isso na coluna de observações e tratar o CIK como chave primária, com o ticker apenas como atributo.
  - 🔗 Hiperlink embutido na célula (alvo exato): `https://www.sec.gov/about/webmaster-frequently-asked-questions`

### FP-08 · SEC SIC Code List

- Origem: aba `Fontes principais`, linha 10 do Excel.
- **#** (coluna A, célula A10): 8
- **Sigla / Nome da base** (coluna B, célula B10): SEC SIC Code List
- **Órgão / mantenedor** (coluna C, célula C10): U.S. SEC
- **Jurisdição** (coluna D, célula D10): EUA
- **Componente IrRAE** (coluna E, célula E10): Prior setorial (setor oficial / núcleo)
- **O que fornece** (coluna F, célula F10): Lista de códigos SIC; o SIC de cada empresa vem no submissions.
- **Link / onde encontrar** (coluna G, célula G10): https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list
- **Tipo de acesso** (coluna H, célula H10): Web / JSON (submissions)
- **Custo** (coluna I, célula I10): Gratuito
- **Status preliminar** (coluna J, célula J10): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K10): Mesma política da SEC.
- **Link dos termos de uso** (coluna L, célula L10): https://www.sec.gov/about/privacy-information
- **Observações** (coluna M, célula M10): Evitar GICS (classificação proprietária MSCI/S&P) para não depender de licença.
- **Sua verificação** (coluna N, célula N10): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O10): GICS e a classficacao de empresas em setor industria etc pela MSCI/S&P

### FP-09 · SEC Form N-PORT Data Sets

- Origem: aba `Fontes principais`, linha 11 do Excel.
- **#** (coluna A, célula A11): 9
- **Sigla / Nome da base** (coluna B, célula B11): SEC Form N-PORT Data Sets
- **Órgão / mantenedor** (coluna C, célula C11): U.S. SEC (DERA)
- **Jurisdição** (coluna D, célula D11): EUA
- **Componente IrRAE** (coluna E, célula E11): Look-through de ETFs/fundos da carteira
- **O que fornece** (coluna F, célula F11): Posições de fundos registrados (ETFs, fundos mútuos) com pesos, identificadores (CUSIP/ISIN/LEI).
- **Link / onde encontrar** (coluna G, célula G11):
```text
https://www.sec.gov/newsroom/whats-new/2407-form-nport-data-sets  (conjuntos em sec.gov → Data & Research → Form N-PORT Data Sets)

https://www.sec.gov/rules-regulations/staff-guidance/official-list-section-13f-securities
```
- **Tipo de acesso** (coluna H, célula H11): Download em lote (zip trimestral)
- **Custo** (coluna I, célula I11): Gratuito
- **Status preliminar** (coluna J, célula J11): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K11): Mesma política da SEC. As posições públicas saem com cerca de 60 dias de atraso.
- **Link dos termos de uso** (coluna L, célula L11): https://www.sec.gov/about/privacy-information
  - 🔗 Hiperlink embutido na célula (alvo exato): `https://www.sec.gov/about/privacy-information`
- **Observações** (coluna M, célula M11): Em 02/2026 a SEC propôs flexibilizar a divulgação do N-PORT (ref. [13] do relatório): acompanhar, pode mudar frequência/defasagem.
- **Sua verificação** (coluna N, célula N11): Pendente
- **Notas da sua pesquisa** (coluna O, célula O11): campo CUSIP/ISIN US sujeito à licença CGS

### FP-10 · SEC Form N-PORT – XML por filing

- Origem: aba `Fontes principais`, linha 12 do Excel.
- **#** (coluna A, célula A12): 10
- **Sigla / Nome da base** (coluna B, célula B12): SEC Form N-PORT – XML por filing
- **Órgão / mantenedor** (coluna C, célula C12): U.S. SEC
- **Jurisdição** (coluna D, célula D12): EUA
- **Componente IrRAE** (coluna E, célula E12): Look-through (fundo a fundo)
- **O que fornece** (coluna F, célula F12): O mesmo N-PORT, arquivo a arquivo, com especificação XML.
- **Link / onde encontrar** (coluna G, célula G12): https://www.sec.gov/info/edgar/specifications/form-n-port-xml-tech-specs.htm
- **Tipo de acesso** (coluna H, célula H12): HTTP (sem chave)
- **Custo** (coluna I, célula I12): Gratuito
- **Status preliminar** (coluna J, célula J12): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K12): Mesma política da SEC.
- **Link dos termos de uso** (coluna L, célula L12): https://www.sec.gov/about/privacy-information
- **Observações** (coluna M, célula M12): Útil para um ETF específico sem baixar o lote inteiro.
- **Sua verificação** (coluna N, célula N12): Pendente
- **Notas da sua pesquisa** (coluna O, célula O12): campo CUSIP/ISIN US sujeito à licença CGS

### FP-11 · SEC Form N-CEN Data Sets

- Origem: aba `Fontes principais`, linha 13 do Excel.
- **#** (coluna A, célula A13): 11
- **Sigla / Nome da base** (coluna B, célula B13): SEC Form N-CEN Data Sets
- **Órgão / mantenedor** (coluna C, célula C13): U.S. SEC (DERA)
- **Jurisdição** (coluna D, célula D13): EUA
- **Componente IrRAE** (coluna E, célula E13): Cadastro de fundos
- **O que fornece** (coluna F, célula F13): Relatório anual de fundos: identifica se o fundo é ETF, índice replicado etc.
- **Link / onde encontrar** (coluna G, célula G13): https://www.sec.gov/about/dera_form_n-cen_data_sets
- **Tipo de acesso** (coluna H, célula H13): Download em lote
- **Custo** (coluna I, célula I13): Gratuito
- **Status preliminar** (coluna J, célula J13): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K13): Mesma política da SEC.
- **Link dos termos de uso** (coluna L, célula L13): https://www.sec.gov/about/privacy-information
- **Observações** (coluna M, célula M13): Auxiliar: confirmar o tipo do fundo antes do look-through.
- **Sua verificação** (coluna N, célula N13): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O13): ∅ (célula vazia)

### FP-12 · USPTO AI Patent Dataset (AIPD)

- Origem: aba `Fontes principais`, linha 14 do Excel.
- **#** (coluna A, célula A14): 12
- **Sigla / Nome da base** (coluna B, célula B14): USPTO AI Patent Dataset (AIPD)
- **Órgão / mantenedor** (coluna C, célula C14): USPTO – Office of the Chief Economist
- **Jurisdição** (coluna D, célula D14): EUA
- **Componente IrRAE** (coluna E, célula E14): R (patentes de IA)
- **O que fornece** (coluna F, célula F14): Classificação de ~15,4 milhões de documentos de patente dos EUA (1976–2023) quanto a conter IA, por categoria (ex.: visão, NLP) e 'any_ai'.
- **Link / onde encontrar** (coluna G, célula G14): https://www.uspto.gov/ip-policy/economic-research/research-datasets/artificial-intelligence-patent-dataset
- **Tipo de acesso** (coluna H, célula H14): Download (CSV/DTA)
- **Custo** (coluna I, célula I14): Gratuito
- **Status preliminar** (coluna J, célula J14): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K14): Termos gerais da USPTO: material do governo dos EUA em domínio público, pode ser copiado com atribuição; nem todo conteúdo do site é do governo. A página pede citação da documentação do AIPD.
- **Link dos termos de uso** (coluna L, célula L14): https://www.uspto.gov/terms-use-uspto-websites
  - 🔗 Hiperlink embutido na célula (alvo exato): `https://www.uspto.gov/terms-use-uspto-websites`
- **Observações** (coluna M, célula M14): Versão AIPD 2023 atualizada em 08/01/2025. Não liga titular → empresa listada: combinar com PatentsView/Assignment/GLEIF.
- **Sua verificação** (coluna N, célula N14): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O14): Obra do governo (OCE/USPTO), domínio público nos EUA; uso só interno como dado. Condições: creditar USPTO e citar o paper do AIPD na metodologia; sem logo/selo; download via bulk. Opcional: confirmar uso comercial com EconomicsData@uspto.gov.
  - 🔗 Hiperlink embutido na célula (alvo exato): `mailto:EconomicsData@uspto.gov`

### FP-13 · USPTO Open Data Portal (ODP) – APIs

- Origem: aba `Fontes principais`, linha 15 do Excel.
- **#** (coluna A, célula A15): 13
- **Sigla / Nome da base** (coluna B, célula B15): USPTO Open Data Portal (ODP) – APIs
- **Órgão / mantenedor** (coluna C, célula C15): USPTO
- **Jurisdição** (coluna D, célula D15): EUA
- **Componente IrRAE** (coluna E, célula E15): R (patentes), titularidade
- **O que fornece** (coluna F, célula F15): Patent File Wrapper, Assignments e diretório de bulk data (substituiu a antiga developer.uspto.gov).
- **Link / onde encontrar** (coluna G, célula G15): https://data.uspto.gov/  |  chave: https://data.uspto.gov/apikey
- **Tipo de acesso** (coluna H, célula H15): API REST com chave gratuita + bulk
- **Custo** (coluna I, célula I15): Gratuito
- **Status preliminar** (coluna J, célula J15): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K15): Termos da USPTO: proibido baixar em massa pelas interfaces web; usar os produtos de bulk. Acesso excessivo pode ser bloqueado sem aviso.
- **Link dos termos de uso** (coluna L, célula L15): https://www.uspto.gov/terms-use-uspto-websites  |  https://data.uspto.gov/support
- **Observações** (coluna M, célula M15): Exige cadastro para a chave de API.
- **Sua verificação** (coluna N, célula N15): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O15): conta USPTO.gov + ID.me desde 18/06/2026; 1 requisição por vez por chave; usar bulk para volume; só metadados, sem documentos do File Wrapper.

### FP-14 · PatentsView – dados desambiguados (agora no ODP)

- Origem: aba `Fontes principais`, linha 16 do Excel.
- **#** (coluna A, célula A16): 14
- **Sigla / Nome da base** (coluna B, célula B16): PatentsView – dados desambiguados (agora no ODP)
- **Órgão / mantenedor** (coluna C, célula C16): USPTO
- **Jurisdição** (coluna D, célula D16): EUA
- **Componente IrRAE** (coluna E, célula E16): R (titular desambiguado)
- **O que fornece** (coluna F, célula F16): Patentes concedidas com titulares (assignees) e inventores desambiguados.
- **Link / onde encontrar** (coluna G, célula G16): https://data.uspto.gov/bulkdata/datasets/pvgpatdis  |  guia: https://data.uspto.gov/support/transition-guide/patentsview
- **Tipo de acesso** (coluna H, célula H16): Bulk (tabelas CSV) + API ODP
- **Custo** (coluna I, célula I16): Gratuito
- **Status preliminar** (coluna J, célula J16): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K16): Mesmos termos da USPTO.
- **Link dos termos de uso** (coluna L, célula L16): https://www.uspto.gov/terms-use-uspto-websites
- **Observações** (coluna M, célula M16): PatentsView migrou para o ODP em 20/03/2026 (ref. [16]). Endpoints antigos podem ter sido desligados.
- **Sua verificação** (coluna N, célula N16): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O16):
```text
O PatentsView traz dados de pessoas físicas: nomes e localização de inventores, e até estimativas de gênero. Os dados de cessão também trazem nomes e endereços de pessoas. Se esses dados forem processados no Brasil, a LGPD se aplica (Lei 13.709/2018, art. 3º). O IrRAE só precisa de empresa → patente. Então a recomendação é baixar só as tabelas de assignees e não importar as de inventores. É o mesmo princípio de minimização que está na nota da Receita

Quem criou: USPTO PatentsView.
Qual é a licença, com link: CC BY 4.0.
Um link para a fonte.
Um aviso de que vocês modificaram os dados, já que vocês agregam e processam.
```

### FP-15 · USPTO Patent Assignment Dataset

- Origem: aba `Fontes principais`, linha 17 do Excel.
- **#** (coluna A, célula A17): 15
- **Sigla / Nome da base** (coluna B, célula B17): USPTO Patent Assignment Dataset
- **Órgão / mantenedor** (coluna C, célula C17): USPTO – Office of the Chief Economist
- **Jurisdição** (coluna D, célula D17): EUA
- **Componente IrRAE** (coluna E, célula E17): R, P (mudança de titular, M&A)
- **O que fornece** (coluna F, célula F17): Registros de cessão/transferência de patentes.
- **Link / onde encontrar** (coluna G, célula G17): https://www.uspto.gov/ip-policy/economic-research/research-datasets/patent-assignment-dataset
- **Tipo de acesso** (coluna H, célula H17): Download (bulk)
- **Custo** (coluna I, célula I17): Gratuito
- **Status preliminar** (coluna J, célula J17): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K17): Mesmos termos da USPTO.
- **Link dos termos de uso** (coluna L, célula L17): https://www.uspto.gov/terms-use-uspto-websites
- **Observações** (coluna M, célula M17): Necessário para atribuir patentes compradas à empresa atual.
- **Sua verificação** (coluna N, célula N17): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O17): crédito à USPTO como boa prática, sem logo, download pelo bulk do ODP e o cuidado com a LGPD..

### FP-15b · Patent Assignment XML

- Origem: aba `Fontes principais`, linha 18 do Excel.
- **#** (coluna A, célula A18): ∅ (célula vazia)
- **Sigla / Nome da base** (coluna B, célula B18): Patent Assignment XML
  - ⚠️ Espaço em branco extra no valor original — início: "\t" · fim: ""
- **Órgão / mantenedor** (coluna C, célula C18): ∅ (célula vazia)
- **Jurisdição** (coluna D, célula D18): EUA
- **Componente IrRAE** (coluna E, célula E18): R, P (mudança de titular, M&A)
- **O que fornece** (coluna F, célula F18): Registros de cessão/transferência de patentes diario, (atualizacao mensal)
- **Link / onde encontrar** (coluna G, célula G18):
```text
https://data.uspto.gov/bulkdata/datasets/pasdl
https://data.uspto.gov/bulkdata/datasets/pasyr
https://data.uspto.gov/bulkdata/datasets/ecorsexc
```
- **Tipo de acesso** (coluna H, célula H18): Download (bulk)
- **Custo** (coluna I, célula I18): Gratuito
- **Status preliminar** (coluna J, célula J18): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K18): Mesmos termos da USPTO. Mais LGPD
- **Link dos termos de uso** (coluna L, célula L18): https://www.uspto.gov/terms-use-uspto-websites  |  https://data.uspto.gov/support
- **Observações** (coluna M, célula M18): Dados brutos diarios ao comparar com o Patent Assignment
- **Sua verificação** (coluna N, célula N18): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O18):
```text
Para o histórico de cessões até 2023, o IrRAE usa o Patent Assignment Dataset da OCE/USPTO, que já vem tabulado e é atualizado uma vez por ano. A partir de 2024, as cessões vêm do Patent Assignment XML (arquivos diários PASDL e anuais PASYR), importado uma vez por mês. As duas bases são de domínio público (Public Domain Mark, catalog.data.gov), sem licença nem taxa. As únicas condições são as dos termos gerais da USPTO: citar o órgão, citar a documentação do dataset (Marco et al., 2015, ssrn.com/abstract=2636461) e não usar o logo ou o selo. O download é feito pelo bulk do ODP, com conta USPTO.gov.

LGPD: as duas bases trazem nomes e endereços de pessoas físicas, principalmente inventores que cedem patentes às empresas. Como o tratamento acontece no Brasil, a LGPD se aplica (Lei 13.709/2018, art. 3º). Por isso, só são importados os registros de pessoas jurídicas, e os dados de pessoas físicas são descartados logo na ingestão.

Impasses:

Junção das bases: o ano de 2023 e o início de 2024 precisam ser conferidos para que nenhuma cessão fique duplicada ou de fora.
Trabalho no XML: os registros vêm brutos. O programador precisa fazer o parsing e classificar o tipo de cada documento pelo texto, separando cessões, fusões e mudanças de nome de garantias, licenças e ônus. Sem esse filtro, uma patente dada em garantia a um banco apareceria como propriedade do banco.
Defasagem: entre uma importação e outra, os dados ficam até um mês desatualizados. Além disso, as cessões só aparecem quando as partes as registram na USPTO, e esse registro pode atrasar.
Mudanças na fonte: a USPTO vem migrando os canais de acesso para o ODP. Endereços de download e formatos de arquivo podem mudar sem aviso, então a rotina mensal deve avisar quando falhar.
```

### FP-16 · GLEIF – LEI e Level 2 (quem é dono de quem)

- Origem: aba `Fontes principais`, linha 19 do Excel.
- **#** (coluna A, célula A19): 16
- **Sigla / Nome da base** (coluna B, célula B19): GLEIF – LEI e Level 2 (quem é dono de quem)
- **Órgão / mantenedor** (coluna C, célula C19): Global Legal Entity Identifier Foundation
- **Jurisdição** (coluna D, célula D19): Internacional (Suíça)
- **Componente IrRAE** (coluna E, célula E19): R, P, C (grupo econômico), identificação
- **O que fornece** (coluna F, célula F19): Identificador LEI de pessoas jurídicas e relações controladora ↔ subsidiária.
- **Link / onde encontrar** (coluna G, célula G19): https://www.gleif.org/en/lei-data/access-and-use-lei-data  |  API: https://api.gleif.org/api/v1/
- **Tipo de acesso** (coluna H, célula H19): API REST sem chave + golden copy (bulk)
- **Custo** (coluna I, célula I19): Gratuito
- **Status preliminar** (coluna J, célula J19): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K19): "The data on GLEIF's website is provided under a Creative Commons (CC0) license" — uso comercial livre, sem exigência de atribuição.
- **Link dos termos de uso** (coluna L, célula L19):
```text
https://www.gleif.org/en/about/open-data

https://www.gleif.org/en/meta/lei-data-terms-of-use
```
  - 🔗 Hiperlink embutido na célula (alvo exato): `https://www.gleif.org/en/about/open-data`
- **Observações** (coluna M, célula M19): Melhor base aberta para montar a tabela titular → empresa. N-PORT também informa LEI das posições.
- **Sua verificação** (coluna N, célula N19): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O19): ∅ (célula vazia)

### FP-17 · OpenFIGI

- Origem: aba `Fontes principais`, linha 20 do Excel.
- **#** (coluna A, célula A20): 17
- **Sigla / Nome da base** (coluna B, célula B20): OpenFIGI
- **Órgão / mantenedor** (coluna C, célula C20): Bloomberg (padrão FIGI, OMG)
- **Jurisdição** (coluna D, célula D20): Internacional (EUA)
- **Componente IrRAE** (coluna E, célula E20): Look-through (identificadores)
- **O que fornece** (coluna F, célula F20): Mapeia CUSIP/ISIN/ticker ↔ FIGI e instrumento.
- **Link / onde encontrar** (coluna G, célula G20): https://www.openfigi.com/api
- **Tipo de acesso** (coluna H, célula H20): API REST (chave gratuita opcional, aumenta limite)
- **Custo** (coluna I, célula I20): Gratuito
- **Status preliminar** (coluna J, célula J20): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K20): FAQ: FIGI incorpora licença MIT; "no cost recovery, licensing or re-use restrictions or hidden fees for access, use, or redistribution of the FIGI symbology". Respeitar limites de requisição da API.
- **Link dos termos de uso** (coluna L, célula L20): https://www.openfigi.com/about/faq  |  https://www.openfigi.com/api/documentation
- **Observações** (coluna M, célula M20): Alternativa aberta ao CUSIP para identificar posições.
- **Sua verificação** (coluna N, célula N20): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O20):
```text
Limites de uso sem chave X com chave (gratuita)

Mapping, requisições	25/min	25 a cada 6 s
Mapping, jobs por requisição	10	100
Search/Filter, requisições	5/min	20/min
Search/Filter, máximo de resultados	15.000	15.000
```

### FP-18 · CUSIP (CUSIP Global Services)

- Origem: aba `Fontes principais`, linha 21 do Excel.
- **#** (coluna A, célula A21): 18
- **Sigla / Nome da base** (coluna B, célula B21): CUSIP (CUSIP Global Services)
- **Órgão / mantenedor** (coluna C, célula C21): CGS / American Bankers Association
- **Jurisdição** (coluna D, célula D21): EUA
- **Componente IrRAE** (coluna E, célula E21): Look-through (identificador presente no N-PORT)
- **O que fornece** (coluna F, célula F21): Identificador de títulos norte-americanos.
- **Link / onde encontrar** (coluna G, célula G21): https://www.cusip.com/services/license-fees.html
- **Tipo de acesso** (coluna H, célula H21): Base comercial
- **Custo** (coluna I, célula I21): Pago (licença)
- **Status preliminar** (coluna J, célula J21): Licença/contrato necessário
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K21): O uso de base de dados CUSIP em produto/serviço pode exigir licença da CGS. Ponto sensível para uso comercial.
- **Link dos termos de uso** (coluna L, célula L21): https://www.cusip.com/legal.html  |  https://www.cusip.com/services/license-fees.html
- **Observações** (coluna M, célula M21): Mitigação: não armazenar/redistribuir CUSIPs; converter para ISIN/FIGI/LEI logo na ingestão e confirmar o entendimento com a CGS.
- **Sua verificação** (coluna N, célula N21): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O21): NAO USAR A PRINCIPIO PORQUE E PAGO, USAR FIGI/LEI E IDENTIFICADOR INTERNOS. CUSIP E ISIN POR SEREM PAGOS NAO DEVERIAM NEM SER ARMAZENADOS NA BASE DO TRACKER

### FP-19 · Preços diários EUA (fornecedor licenciado)

- Origem: aba `Fontes principais`, linha 22 do Excel.
- **#** (coluna A, célula A22): 19
- **Sigla / Nome da base** (coluna B, célula B22): Preços diários EUA (fornecedor licenciado)
- **Órgão / mantenedor** (coluna C, célula C22): Ex.: Nasdaq Data Link, Tiingo, Alpha Vantage, CRSP/WRDS
- **Jurisdição** (coluna D, célula D22): EUA
- **Componente IrRAE** (coluna E, célula E22): Auditoria por retornos (seção 5.10)
- **O que fornece** (coluna F, célula F22): Séries de preços/retornos diários de ações e índices setoriais.
- **Link / onde encontrar** (coluna G, célula G22): Site de cada fornecedor (planos comerciais)
- **Tipo de acesso** (coluna H, célula H22): API (chave)
- **Custo** (coluna I, célula I22): Pago (varia)
- **Status preliminar** (coluna J, célula J22): Licença/contrato necessário
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K22): Dados de preço são licenciados pelo fornecedor/bolsa. CRSP via WRDS é, em geral, só para uso acadêmico. Yahoo Finance: termos não permitem uso comercial automatizado — evitar.
- **Link dos termos de uso** (coluna L, célula L22): Termos de cada fornecedor
- **Observações** (coluna M, célula M22): Na v1.1 os retornos são só auditoria; o modelo roda sem preços.
- **Sua verificação** (coluna N, célula N22): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O22): dado pago de cotacoes, por enquanto desnecessario

### FP-20 · NAICS

- Origem: aba `Fontes principais`, linha 23 do Excel.
- **#** (coluna A, célula A23): 20
- **Sigla / Nome da base** (coluna B, célula B23): NAICS
- **Órgão / mantenedor** (coluna C, célula C23): U.S. Census Bureau
- **Jurisdição** (coluna D, célula D23): EUA
- **Componente IrRAE** (coluna E, célula E23): Prior setorial (alternativa ao SIC)
- **O que fornece** (coluna F, célula F23): Classificação setorial norte-americana.
- **Link / onde encontrar** (coluna G, célula G23): https://www.census.gov/naics/
- **Tipo de acesso** (coluna H, célula H23): Download / web
- **Custo** (coluna I, célula I23): Gratuito
- **Status preliminar** (coluna J, célula J23): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K23): Obra do governo dos EUA (17 U.S.C. §105), em princípio domínio público — confirmar.
- **Link dos termos de uso** (coluna L, célula L23): https://www.census.gov/data/developers/about/terms-of-service.html
- **Observações** (coluna M, célula M23): Opcional; útil se o SIC for grosseiro demais.
- **Sua verificação** (coluna N, célula N23): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O23): All services, which utilize or access the API, should display the following notice prominently within the application: "This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau." You may use the Census Bureau name in order to identify the source of API content subject to these rules. You may not use the Census Bureau name, or the like to imply endorsement of any product, service, or entity, not-for-profit, commercial or otherwise.

### FP-21 · CVM Dados Abertos – DFP (Demonstrações Financeiras Padronizadas)

- Origem: aba `Fontes principais`, linha 24 do Excel.
- **#** (coluna A, célula A24): 21
- **Sigla / Nome da base** (coluna B, célula B24): CVM Dados Abertos – DFP (Demonstrações Financeiras Padronizadas)
- **Órgão / mantenedor** (coluna C, célula C24): CVM
- **Jurisdição** (coluna D, célula D24): Brasil
- **Componente IrRAE** (coluna E, célula E24): A, Ir (DFC: aquisição de imobilizado)
- **O que fornece** (coluna F, célula F24): Balanço, DRE, DFC anuais de companhias abertas, estruturados.
- **Link / onde encontrar** (coluna G, célula G24): https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp
- **Tipo de acesso** (coluna H, célula H24): Download em lote (CSV, zip anual)
- **Custo** (coluna I, célula I24): Gratuito
- **Status preliminar** (coluna J, célula J24): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K24): Licença ODbL (Open Database License): uso comercial permitido, com atribuição; base derivada divulgada publicamente deve manter a ODbL (share-alike). Base legal: LAI (Lei 12.527/2011) e Decreto 8.777/2016.
- **Link dos termos de uso** (coluna L, célula L24): https://dados.cvm.gov.br/about  |  https://opendatacommons.org/licenses/odbl/
- **Observações** (coluna M, célula M24): Segmentos (CPC 22 / IFRS 8) ficam nas notas explicativas (PDF, ver RAD/ENET), não no CSV estruturado.
- **Sua verificação** (coluna N, célula N24): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O24): ∅ (célula vazia)

### FP-22 · CVM Dados Abertos – ITR (Informações Trimestrais)

- Origem: aba `Fontes principais`, linha 25 do Excel.
- **#** (coluna A, célula A25): 22
- **Sigla / Nome da base** (coluna B, célula B25): CVM Dados Abertos – ITR (Informações Trimestrais)
- **Órgão / mantenedor** (coluna C, célula C25): CVM
- **Jurisdição** (coluna D, célula D25): Brasil
- **Componente IrRAE** (coluna E, célula E25): A, Ir
- **O que fornece** (coluna F, célula F25): Demonstrações trimestrais estruturadas.
- **Link / onde encontrar** (coluna G, célula G25): https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr
- **Tipo de acesso** (coluna H, célula H25): Download em lote (CSV)
- **Custo** (coluna I, célula I25): Gratuito
- **Status preliminar** (coluna J, célula J25): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K25): ODbL (ver DFP).
- **Link dos termos de uso** (coluna L, célula L25): https://dados.cvm.gov.br/about
- **Observações** (coluna M, célula M25): Para séries trimestrais e Kalman (seção 5.11).
- **Sua verificação** (coluna N, célula N25): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O25): ∅ (célula vazia)

### FP-23 · CVM Dados Abertos – FRE (Formulário de Referência)

- Origem: aba `Fontes principais`, linha 26 do Excel.
- **#** (coluna A, célula A26): 23
- **Sigla / Nome da base** (coluna B, célula B26): CVM Dados Abertos – FRE (Formulário de Referência)
- **Órgão / mantenedor** (coluna C, célula C26): CVM
- **Jurisdição** (coluna D, célula D26): Brasil
- **Componente IrRAE** (coluna E, célula E26): N, C, P, A (segmentos), prior
- **O que fornece** (coluna F, célula F26): Descrição das atividades, segmentos operacionais, clientes relevantes, controladas/participações, comentários dos diretores.
- **Link / onde encontrar** (coluna G, célula G26): https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre
- **Tipo de acesso** (coluna H, célula H26): Download em lote (CSV)
- **Custo** (coluna I, célula I26): Gratuito
- **Status preliminar** (coluna J, célula J26): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K26): ODbL (ver DFP).
- **Link dos termos de uso** (coluna L, célula L26): https://dados.cvm.gov.br/about
- **Observações** (coluna M, célula M26): Equivalente brasileiro mais próximo do Item 1 do 10-K: principal fonte de N e C no Brasil.
- **Sua verificação** (coluna N, célula N26): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O26): ∅ (célula vazia)

### FP-24 · CVM Dados Abertos – Cadastro de Companhias Abertas

- Origem: aba `Fontes principais`, linha 27 do Excel.
- **#** (coluna A, célula A27): 24
- **Sigla / Nome da base** (coluna B, célula B27): CVM Dados Abertos – Cadastro de Companhias Abertas
- **Órgão / mantenedor** (coluna C, célula C27): CVM
- **Jurisdição** (coluna D, célula D27): Brasil
- **Componente IrRAE** (coluna E, célula E27): Cadastro, prior setorial
- **O que fornece** (coluna F, célula F27): CNPJ, código CVM, setor de atividade, situação.
- **Link / onde encontrar** (coluna G, célula G27): https://dados.cvm.gov.br/dataset/cia_aberta-cad
- **Tipo de acesso** (coluna H, célula H27): Download (CSV)
- **Custo** (coluna I, célula I27): Gratuito
- **Status preliminar** (coluna J, célula J27): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K27): ODbL (ver DFP).
- **Link dos termos de uso** (coluna L, célula L27): https://dados.cvm.gov.br/about
- **Observações** (coluna M, célula M27): Chave de ligação CVM ↔ CNPJ ↔ ticker B3.
- **Sua verificação** (coluna N, célula N27): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O27): ∅ (célula vazia)

### FP-25 · CVM Dados Abertos – CDA (Composição e Diversificação das Aplicações)

- Origem: aba `Fontes principais`, linha 28 do Excel.
- **#** (coluna A, célula A28): 25
- **Sigla / Nome da base** (coluna B, célula B28): CVM Dados Abertos – CDA (Composição e Diversificação das Aplicações)
- **Órgão / mantenedor** (coluna C, célula C28): CVM
- **Jurisdição** (coluna D, célula D28): Brasil
- **Componente IrRAE** (coluna E, célula E28): Look-through de fundos e ETFs brasileiros
- **O que fornece** (coluna F, célula F28): Carteiras mensais dos fundos de investimento (inclui fundos de índice/ETFs).
- **Link / onde encontrar** (coluna G, célula G28): https://dados.cvm.gov.br/dataset/fi-doc-cda
  - 🔗 Hiperlink embutido na célula (alvo exato): `https://dados.cvm.gov.br/dataset/fi-doc-cda`
- **Tipo de acesso** (coluna H, célula H28): Download em lote (CSV mensal)
- **Custo** (coluna I, célula I28): Gratuito
- **Status preliminar** (coluna J, célula J28): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K28): ODbL (ver DFP).
- **Link dos termos de uso** (coluna L, célula L28): https://dados.cvm.gov.br/about
- **Observações** (coluna M, célula M28): A regulamentação permite omitir temporariamente algumas posições (aplicações confidenciais) — verificar prazo vigente; tratar o omitido como 'não coberto'.
- **Sua verificação** (coluna N, célula N28): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O28):
```text
Os detalhes sobre as aplicações individualizadas somente estarão disponíveis após expirado o prazo de confidencialidade solicitado pelos administradores dos fundos no envio das informações à CVM. As aplicações sob restrição de confidencialidade serão exibidas de forma consolidada no arquivo cda_fi_CONFID_AAAAMM.csv.

(A partir de 04/03/2024): As aplicações dos fundos de índice (FIIM), competência 06/2018 em diante, estarão disponíveis nos seguintes arquivos: cda_fiim_AAAAMM.csv (independente do bloco a que pertencem) e cda_fiim_CONFID_AAAAMM.csv (durante a vigência do prazo de confidencialidade).

(A partir de 08/11/2025): As aplicações dos fundos FIDC e FIAGRO também foram incluídas nos arquivos cda_fiim_AAAAMM.csv e cda_fiim_CONFID_AAAAMM.csv. A partir de 15/11/2025, os arquivos serão renomeados para cda_fie_AAAAMM.csv e cda_fie_CONFID_AAAAMM.csv

O conjunto de dados disponibiliza as carteiras dos Fundos de Investimento nos últimos doze meses.

Os arquivos referentes aos três meses mais recentes (M-1, M-2, M-3) serão atualizados diariamente com as eventuais reapresentações. A atualização ocorre de terça a sábado, às 08:00h, com os dados recebidos pelo CVMWeb até as 23:59h do dia anterior.

Os arquivos referentes aos meses M-4, M-5, ..., até M-12 serão atualizados semanalmente com as eventuais reapresentações. A atualização ocorre toda segunda-feira, às 08:00h, com os dados recebidos pelo CVMWeb na semana anterior.
```

### FP-26 · CVM Dados Abertos – Cadastro de Fundos

- Origem: aba `Fontes principais`, linha 29 do Excel.
- **#** (coluna A, célula A29): 26
- **Sigla / Nome da base** (coluna B, célula B29): CVM Dados Abertos – Cadastro de Fundos
- **Órgão / mantenedor** (coluna C, célula C29): CVM
- **Jurisdição** (coluna D, célula D29): Brasil
- **Componente IrRAE** (coluna E, célula E29): Cadastro de fundos
- **O que fornece** (coluna F, célula F29): Tipo/classe do fundo (identifica ETFs), CNPJ, gestor.
- **Link / onde encontrar** (coluna G, célula G29): https://dados.cvm.gov.br/dataset/fi-cad  (ou busca 'cadastro de fundos' no portal)
  - 🔗 Hiperlink embutido na célula (alvo exato): `https://dados.cvm.gov.br/dataset/fi-cad%20%20(ou%20busca%20'cadastro%20de%20fundos'%20no%20portal)`
- **Tipo de acesso** (coluna H, célula H29): Download (CSV)
- **Custo** (coluna I, célula I29): Gratuito
- **Status preliminar** (coluna J, célula J29): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K29): ODbL (ver DFP).+K29
- **Link dos termos de uso** (coluna L, célula L29): https://dados.cvm.gov.br/about
- **Observações** (coluna M, célula M29): Após a Resolução CVM 175 os cadastros mudaram de estrutura (fundo/classe/subclasse).
- **Sua verificação** (coluna N, célula N29): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O29): atualização dos arquivos ocorre de terça a sábado, às 08:00h, com a posição cadastral dos fundos até as 23:59h do dia anterior.

### FP-27 · CVM RAD / Empresas.NET (documentos entregues)

- Origem: aba `Fontes principais`, linha 30 do Excel.
- **#** (coluna A, célula A30): 27
- **Sigla / Nome da base** (coluna B, célula B30): CVM RAD / Empresas.NET (documentos entregues)
- **Órgão / mantenedor** (coluna C, célula C30): CVM
- **Jurisdição** (coluna D, célula D30): Brasil
- **Componente IrRAE** (coluna E, célula E30): A (notas de segmentos), N, B
- **O que fornece** (coluna F, célula F30): PDFs de DFP/ITR com notas explicativas, releases, fatos relevantes.
- **Link / onde encontrar** (coluna G, célula G30): [CÉLULA CONTÉM APENAS ESPAÇO EM BRANCO: " "]
- **Tipo de acesso** (coluna H, célula H30): Web (sem API oficial)
- **Custo** (coluna I, célula I30): Gratuito
- **Status preliminar** (coluna J, célula J30): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K30): Documentos públicos, mas não há API documentada; coleta automatizada (raspagem) depende dos termos do sistema — verificar.
- **Link dos termos de uso** (coluna L, célula L30): Termos dos sistemas CVM (ex.: https://cvmweb.cvm.gov.br/static/geral/CVMWEB-TU-v20220810.pdf)
- **Observações** (coluna M, célula M30): Onde estão as notas de segmentos das empresas brasileiras.
- **Sua verificação** (coluna N, célula N30): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O30): Nao achei nada sobre comercial e API
  - ⚠️ Espaço em branco extra no valor original — início: "" · fim: " "

### FP-28 · B3 – Cotações Históricas (COTAHIST)

- Origem: aba `Fontes principais`, linha 31 do Excel.
- **#** (coluna A, célula A31): 28
- **Sigla / Nome da base** (coluna B, célula B31): B3 – Cotações Históricas (COTAHIST)
- **Órgão / mantenedor** (coluna C, célula C31): B3
- **Jurisdição** (coluna D, célula D31): Brasil
- **Componente IrRAE** (coluna E, célula E31): Auditoria por retornos (preços BR)
- **O que fornece** (coluna F, célula F31): Arquivo diário/anual com cotações de todos os papéis negociados.
- **Link / onde encontrar** (coluna G, célula G31): https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/
- **Tipo de acesso** (coluna H, célula H31): Download (TXT, layout fixo)
- **Custo** (coluna I, célula I31): Gratuito (download)
- **Status preliminar** (coluna J, célula J31): Licença/contrato necessário
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K31): Política Comercial de Market Data B3 (v3.0.4): dados históricos e de fim de dia podem ser distribuídos livremente, MAS "usage of B3 market data is not permitted ... for the creation, calculation or commercialization of indexes or other derived data" sem autorização.
- **Link dos termos de uso** (coluna L, célula L31): https://www.b3.com.br/data/files/EF/77/94/75/0AB929106EEC8429AC094EA8/Market%20Data%20Commercial%20Policy%20v3.0.4.1.pdf
- **Observações** (coluna M, célula M31): Um escore comercial calculado com preços B3 pode ser 'dado derivado' — consultar produtosdedados@b3.com.br.
- **Sua verificação** (coluna N, célula N31): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O31):
```text
Licença (Mercado à Vista, mensal, por dataset)	Valor
Distribuição em Atraso, Snapshot	R$ 320
Distribuição em Atraso, Contínuo	R$ 1.920
Distribuição em Tempo Real	R$ 6.000

Por enquanto nao e necessario os dados historicos
```

### FP-29 · B3 – BDRs e ETFs listados (e carteiras dos ETFs)

- Origem: aba `Fontes principais`, linha 32 do Excel.
- **#** (coluna A, célula A32): 29
- **Sigla / Nome da base** (coluna B, célula B32): B3 – BDRs e ETFs listados (e carteiras dos ETFs)
- **Órgão / mantenedor** (coluna C, célula C32): B3 / gestores dos ETFs
- **Jurisdição** (coluna D, célula D32): Brasil
- **Componente IrRAE** (coluna E, célula E32): Look-through (carteira do investidor brasileiro)
- **O que fornece** (coluna F, célula F32): Lista de BDRs (ativo estrangeiro de lastro) e ETFs; composição de ETFs de índice.
- **Link / onde encontrar** (coluna G, célula G32): Onde achar: b3.com.br → Produtos e Serviços → Negociação → Renda Variável → BDRs / ETFs; carteira do ETF no site do gestor
- **Tipo de acesso** (coluna H, célula H32): Web / arquivos
- **Custo** (coluna I, célula I32): Gratuito
- **Status preliminar** (coluna J, célula J32): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K32): Sujeito à Política de Market Data B3 (ver COTAHIST) e aos termos de cada gestor.
- **Link dos termos de uso** (coluna L, célula L32): Política Comercial de Market Data B3
- **Observações** (coluna M, célula M32): Essencial para o investidor brasileiro: BDR de NVDA → aplicar o IrRAE da NVDA; ETF BR de índice americano → abrir carteira.
- **Sua verificação** (coluna N, célula N32): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O32):
```text
Confirmem se os ETFs estão no CDA. Os ETFs têm regras próprias no Anexo Normativo V da Resolução CVM 175, então não assumi que entram no mesmo arquivo. O teste é simples: procurem o CNPJ de um ETF conhecido (o do BOVA11, por exemplo) dentro do arquivo.
Frequência mensal, com defasagem. Serve para exposição temática; não serve para composição diária.
Risco regulatório. A CVM propôs manter a entrega mensal da carteira para ela, mas flexibilizar a divulgação ao mercado. Se isso mudar o que vai para os Dados Abertos, a fonte pode piorar. Acompanhem.
Obrigações da ODbL (meu conhecimento da licença, não verificado nesta conversa): exige atribuição. Se vocês publicarem uma base derivada, ela precisa sair também sob ODbL. Gráficos e scores exibidos no produto contam como "trabalho produzido" e pedem só o aviso de atribuição. Vale confirmar com o advogado como isso se aplica ao produto de vocês.

Como a composicao diaria dos ETFs pela B3 requer licenca de produto, use o CDA da CVM sob a licenca ODbL Para BDRs fazer teste com 20 tickers mapeando o lastro pelo OpenFIGI (licenca MIT) e verificar se esse metodo funciona
```

### FP-30 · B3 – Composição de índices (carteira teórica)

- Origem: aba `Fontes principais`, linha 33 do Excel.
- **#** (coluna A, célula A33): 30
- **Sigla / Nome da base** (coluna B, célula B33): B3 – Composição de índices (carteira teórica)
- **Órgão / mantenedor** (coluna C, célula C33): B3
- **Jurisdição** (coluna D, célula D33): Brasil
- **Componente IrRAE** (coluna E, célula E33): Look-through de ETFs de índice; fator do setor oficial BR
- **O que fornece** (coluna F, célula F33): Carteira teórica e pesos de Ibovespa e índices setoriais.
- **Link / onde encontrar** (coluna G, célula G33): Onde achar: b3.com.br → Market Data e Índices → Índices
- **Tipo de acesso** (coluna H, célula H33): Web / arquivos
- **Custo** (coluna I, célula I33): Gratuito (consulta)
- **Status preliminar** (coluna J, célula J33): Licença/contrato necessário
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K33): Índices B3 são marcas/produtos da B3; uso para produto derivado costuma exigir licença de índice.
- **Link dos termos de uso** (coluna L, célula L33): Política Comercial de Market Data B3 / licenciamento de índices B3
- **Observações** (coluna M, célula M33): Para ETFs brasileiros que replicam índice, a carteira do índice é um atalho ao CDA.
- **Sua verificação** (coluna N, célula N33): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O33): Tudo da B3 para uso comercial tem um custo. Para a V1 do prototipo nao tem necessidade dos dados de etf virem pela B3. A CVM cobre os pesos de indices (1 mes de atraso), os precos sao dados  pelo usuario e exlcusivamente do usuario entao nao precisa de licenca de cotacao por hora. E as benchaamarks padrao de CDI, Selic e IPCA tambem sao publicas

### FP-31 · ISIN – Brasil (B3 como agência numeradora)

- Origem: aba `Fontes principais`, linha 34 do Excel.
- **#** (coluna A, célula A34): 31
- **Sigla / Nome da base** (coluna B, célula B34): ISIN – Brasil (B3 como agência numeradora)
- **Órgão / mantenedor** (coluna C, célula C34): B3
- **Jurisdição** (coluna D, célula D34): Brasil
- **Componente IrRAE** (coluna E, célula E34): Identificação de ativos
- **O que fornece** (coluna F, célula F34): Códigos ISIN de ativos brasileiros.
- **Link / onde encontrar** (coluna G, célula G34): Onde achar: site da B3 → serviço de Codificação ISIN
- **Tipo de acesso** (coluna H, célula H34): Web / arquivo
- **Custo** (coluna I, célula I34): Gratuito (consulta)
- **Status preliminar** (coluna J, célula J34): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K34): Verificar termos de uso do serviço de consulta de ISIN da B3.
- **Link dos termos de uso** (coluna L, célula L34): Site B3
- **Observações** (coluna M, célula M34): Ligar posições do CDA a empresas; combinar com OpenFIGI.
- **Sua verificação** (coluna N, célula N34): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O34): Para ISIN Brasil tem que armazenar internamente pelo ISIN dado pelo proprio usario em um CSV. Ele serve como tentatativa de catalogacao, mas caso o codigo recebesse um ticker sem ISIN ele deveria criar um codigo interno prorpio ou 'algo assim. Tambem e necessario usar o senso comum em casos como BBDC3 e BBDC3F, onde o F nao e um outro ticker e sim uma fracao do principal

### FP-32 · INPI – Dados Abertos (patentes)

- Origem: aba `Fontes principais`, linha 35 do Excel.
- **#** (coluna A, célula A35): 32
- **Sigla / Nome da base** (coluna B, célula B35): INPI – Dados Abertos (patentes)
- **Órgão / mantenedor** (coluna C, célula C35): INPI
- **Jurisdição** (coluna D, célula D35): Brasil
- **Componente IrRAE** (coluna E, célula E35): R (patentes brasileiras)
- **O que fornece** (coluna F, célula F35): Pedidos e concessões de patentes no Brasil, titulares, classificação IPC.
- **Link / onde encontrar** (coluna G, célula G35): https://dadosabertos.inpi.gov.br/  |  https://www.gov.br/inpi/pt-br/acesso-a-informacao/dados-abertos
- **Tipo de acesso** (coluna H, célula H35): https://dadosabertos.inpi.gov.br/  |  https://www.gov.br/inpi/pt-br/acesso-a-informacao/dados-abertos
- **Custo** (coluna I, célula I35): Gratuito
- **Status preliminar** (coluna J, célula J35): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K35): O conteúdo do site do INPI está sob CC BY-ND 3.0 (sem derivações) — confirmar se a mesma licença vale para os conjuntos de dados; 'ND' poderia restringir bases derivadas. Base legal: LAI e Decreto 8.777/2016.
- **Link dos termos de uso** (coluna L, célula L35): https://www.gov.br/inpi/pt-br/acesso-a-informacao/dados-abertos
- **Observações** (coluna M, célula M35): Não há um equivalente ao AIPD: classificar IA por IPC/CPC (ex.: G06N) ou por texto.
- **Sua verificação** (coluna N, célula N35): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O35): Uso livre, so nao sendo permitido usar logo do INPI e edicar e copiar textos. Ter muito cuidado com LGPD, apagar CPF e dados de PF ja na ingestao dos dados

### FP-33 · INPI – BuscaWeb (pePI)

- Origem: aba `Fontes principais`, linha 36 do Excel.
- **#** (coluna A, célula A36): 33
- **Sigla / Nome da base** (coluna B, célula B36): INPI – BuscaWeb (pePI)
- **Órgão / mantenedor** (coluna C, célula C36): INPI
- **Jurisdição** (coluna D, célula D36): Brasil
- **Componente IrRAE** (coluna E, célula E36): R (consulta pontual)
- **O que fornece** (coluna F, célula F36): Consulta de processos de patente.
- **Link / onde encontrar** (coluna G, célula G36): https://busca.inpi.gov.br/pePI/
- **Tipo de acesso** (coluna H, célula H36): Web (sem API)
- **Custo** (coluna I, célula I36): Gratuito
- **Status preliminar** (coluna J, célula J36): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K36): Consulta pública; raspagem automatizada não recomendada sem verificar termos.
- **Link dos termos de uso** (coluna L, célula L36): Site do INPI
- **Observações** (coluna M, célula M36): Usar só para conferência manual.
- **Sua verificação** (coluna N, célula N36): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O36): Nao aceita robos, so serve para consulta manual poontual

### FP-34 · Receita Federal – Dados Abertos do CNPJ

- Origem: aba `Fontes principais`, linha 37 do Excel.
- **#** (coluna A, célula A37): 34
- **Sigla / Nome da base** (coluna B, célula B37): Receita Federal – Dados Abertos do CNPJ
- **Órgão / mantenedor** (coluna C, célula C37): Receita Federal do Brasil
- **Jurisdição** (coluna D, célula D37): Brasil
- **Componente IrRAE** (coluna E, célula E37): P, R (titular CNPJ → grupo), prior (CNAE)
- **O que fornece** (coluna F, célula F37): Empresas, estabelecimentos, CNAE, quadro de sócios (QSA).
- **Link / onde encontrar** (coluna G, célula G37): https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/  |  metadados: https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf
- **Tipo de acesso** (coluna H, célula H37): Download em lote (CSV, mensal)
- **Custo** (coluna I, célula I37): Gratuito
- **Status preliminar** (coluna J, célula J37): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K37): Dados abertos (LAI, Decreto 8.777/2016). O QSA contém dados de pessoas físicas: tratamento sujeito à LGPD (Lei 13.709/2018) — usar só dados de pessoas jurídicas e minimizar.
- **Link dos termos de uso** (coluna L, célula L37): https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos
- **Observações** (coluna M, célula M37): Liga titulares de patentes do INPI (CNPJ) ao grupo econômico.
- **Sua verificação** (coluna N, célula N37): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O37):
```text
Na prática, para o Sagital
Filtre pelo universo que interessa. Faça o join pelo CNPJ com o cadastro de companhias abertas da CVM e com os CNPJs de FIIs e fundos. Isso já elimina quase todo empresário individual e MEI.
Exclua na ingestão os registros com natureza jurídica de empresário individual e os optantes pelo MEI (tabela do Simples).
Não guarde a tabela de Sócios, nem e-mail e telefone dos estabelecimentos. Para análise de investimento, você só precisa de CNAE, natureza jurídica, situação cadastral, capital social, porte, data de abertura, município e número de filiais.
Não use os contatos para marketing. Isso foge da finalidade da publicação (LGPD, art. 7º, §3º) e é o tipo de uso que mais gera reclamação.
Crédito: exiba “Fonte: Receita Federal, Dados Abertos do CNPJ”.
```

### FP-35 · IBGE – CNAE (CONCLA) e API de serviços

- Origem: aba `Fontes principais`, linha 38 do Excel.
- **#** (coluna A, célula A38): 35
- **Sigla / Nome da base** (coluna B, célula B38): IBGE – CNAE (CONCLA) e API de serviços
- **Órgão / mantenedor** (coluna C, célula C38): IBGE
- **Jurisdição** (coluna D, célula D38): Brasil
- **Componente IrRAE** (coluna E, célula E38): Prior setorial BR
- **O que fornece** (coluna F, célula F38): Classificação Nacional de Atividades Econômicas.
- **Link / onde encontrar** (coluna G, célula G38): https://servicodados.ibge.gov.br/api/docs/cnae  |  https://concla.ibge.gov.br/
- **Tipo de acesso** (coluna H, célula H38): API REST sem chave
- **Custo** (coluna I, célula I38): Gratuito
- **Status preliminar** (coluna J, célula J38): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K38): Dado público do IBGE; confirmar termos de uso da API.
- **Link dos termos de uso** (coluna L, célula L38): https://servicodados.ibge.gov.br/api/docs
- **Observações** (coluna M, célula M38): Equivalente brasileiro do SIC.
- **Sua verificação** (coluna N, célula N38): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O38):
```text
Necessidade	Fonte recomendada
Código CNAE das empresas (principal e secundários)	Base do CNPJ (Receita), tabela Estabelecimentos
Descrição dos códigos	Tabela de domínio “CNAEs” que vem no próprio pacote da Receita
Hierarquia (seção → divisão → grupo → classe → subclasse) para agrupar por setor	API do IBGE ou download da estrutura no CONCLA

Dicas de implementação:

Baixe a estrutura uma vez e guarde localmente. A CNAE muda raramente, então não faz sentido chamar a API a cada consulta, e isso evita depender da disponibilidade do IBGE.
Use a hierarquia para montar “setores”. Por exemplo, a divisão 35 (eletricidade e gás) agrupa Copel, AXIA e outras.
O CNAE não é a classificação setorial da B3. A B3 tem a própria classificação (Utilidade Pública > Energia Elétrica). Para o investidor, a da B3 é mais familiar, mas é dado da B3 e cai nas mesmas restrições de uso que discutimos. Uma alternativa é montar o seu próprio mapa de setores a partir do CNAE.
Crédito: exiba “Fonte: IBGE/CONCLA, CNAE 2.3” e confirme a versão vigente no site.Dicas de implementação:

Baixe a estrutura uma vez e guarde localmente. A CNAE muda raramente, então não faz sentido chamar a API a cada consulta, e isso evita depender da disponibilidade do IBGE.
Use a hierarquia para montar “setores”. Por exemplo, a divisão 35 (eletricidade e gás) agrupa Copel, AXIA e outras.
O CNAE não é a classificação setorial da B3. A B3 tem a própria classificação (Utilidade Pública > Energia Elétrica). Para o investidor, a da B3 é mais familiar, mas é dado da B3 e cai nas mesmas restrições de uso que discutimos. Uma alternativa é montar o seu próprio mapa de setores a partir do CNAE.
Crédito: exiba “Fonte: IBGE/CONCLA, CNAE 2.3” e confirme a versão vigente no site.
```
  - ⚠️ Espaço em branco extra no valor original — início: "" · fim: "\n\n\n "

### FP-36 · BCB – SGS / PTAX (Olinda)

- Origem: aba `Fontes principais`, linha 39 do Excel.
- **#** (coluna A, célula A39): 36
- **Sigla / Nome da base** (coluna B, célula B39): BCB – SGS / PTAX (Olinda)
- **Órgão / mantenedor** (coluna C, célula C39): Banco Central do Brasil
- **Jurisdição** (coluna D, célula D39): Brasil
- **Componente IrRAE** (coluna E, célula E39): Conversão cambial da carteira
- **O que fornece** (coluna F, célula F39): Câmbio PTAX e séries macro (SGS).
- **Link / onde encontrar** (coluna G, célula G39): https://dadosabertos.bcb.gov.br/  |  SGS: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json
- **Tipo de acesso** (coluna H, célula H39): API REST sem chave
- **Custo** (coluna I, célula I39): Gratuito
- **Status preliminar** (coluna J, célula J39): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K39): Dados abertos do BCB (Decreto 8.777/2016); confirmar a licença indicada em cada conjunto no portal.
- **Link dos termos de uso** (coluna L, célula L39): https://dadosabertos.bcb.gov.br/
- **Observações** (coluna M, célula M39): Converter posições em USD (BDRs, ativos no exterior) para BRL ao calcular os pesos ω.
- **Sua verificação** (coluna N, célula N39): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O39):
```text
Pelo levantamento que encontrei, o BCB apura a PTAX apenas do dólar. As paridades das outras moedas (euro, libra etc.) vêm da Refinitiv/LSEG e são só redistribuídas pelo BCB.
Use livremente: PTAX do USD. Com cautela: EUR, GBP e outras.
O aviso de responsabilidade que vem nas respostas da API Olinda deve ser repassado ao usuário.
```

### FP-37 · ANBIMA Feed / ANBIMA Data

- Origem: aba `Fontes principais`, linha 40 do Excel.
- **#** (coluna A, célula A40): 37
- **Sigla / Nome da base** (coluna B, célula B40): ANBIMA Feed / ANBIMA Data
- **Órgão / mantenedor** (coluna C, célula C40): ANBIMA
- **Jurisdição** (coluna D, célula D40): Brasil
- **Componente IrRAE** (coluna E, célula E40): Cadastro e classificação de fundos
- **O que fornece** (coluna F, célula F40): Dados de fundos (cadastro, classificação ANBIMA, rentabilidade).
- **Link / onde encontrar** (coluna G, célula G40): https://feed.anbima.com.br/  |  https://data.anbima.com.br/  |  https://developers.anbima.com.br/
- **Tipo de acesso** (coluna H, célula H40): API (contrato)
- **Custo** (coluna I, célula I40): Pago (contrato)
- **Status preliminar** (coluna J, célula J40): Licença/contrato necessário
- **Validade jurídica (leitura preliminar — confirmar)** (coluna K, célula K40): Produto comercial da ANBIMA; uso via contrato/licença.
- **Link dos termos de uso** (coluna L, célula L40): Termos no ANBIMA Developers / contrato
- **Observações** (coluna M, célula M40): Opcional: o CDA da CVM já cobre as carteiras gratuitamente.
- **Sua verificação** (coluna N, célula N40): VALIDADO
- **Notas da sua pesquisa** (coluna O, célula O40): a CVM cobre praticamente todos os fundos regulados, de graça e com licença aberta (ODbL). O que ela não tem são as criações da própria ANBIMA: a classificação ANBIMA e os índices IMA, IDA e IHFA.

## Seção 3 — Aba `Fontes adicionais` (10 fichas, transcrição integral)

Título da aba (célula A1): **Fontes adicionais confiáveis (não previstas no relatório v1)**

Colunas da aba, na ordem do Excel: A = `#` · B = `Sigla / Nome da base` · C = `Órgão / mantenedor` · D = `Jurisdição` · E = `O que fornece` · F = `Link / onde encontrar` · G = `Tipo de acesso` · H = `Custo` · I = `Status preliminar` · J = `Validade jurídica (leitura preliminar — confirmar)` · K = `Para que serviria no IrRAE` · L = `Sua verificação` · M = `Notas da sua pesquisa`

Lista suspensa definida no Excel para L3:L12: "Pendente,Aprovado,Aprovado com condições,Reprovado" (valores não listados, como `VALIDADO`, foram digitados manualmente).

### FA-01 · EPO Open Patent Services (OPS)

- Origem: aba `Fontes adicionais`, linha 3 do Excel.
- **#** (coluna A, célula A3): 1
- **Sigla / Nome da base** (coluna B, célula B3): EPO Open Patent Services (OPS)
- **Órgão / mantenedor** (coluna C, célula C3): European Patent Office
- **Jurisdição** (coluna D, célula D3): Internacional (Europa)
- **O que fornece** (coluna E, célula E3): Patentes no mundo todo (INPADOC/DOCDB) para empresas não americanas e famílias de patentes.
- **Link / onde encontrar** (coluna F, célula F3): https://www.epo.org/en/searching-for-patents/data/web-services/ops
- **Tipo de acesso** (coluna G, célula G3): API (cadastro)
- **Custo** (coluna H, célula H3): Gratuito até cota semanal (fair use); acima, pago
- **Status preliminar** (coluna I, célula I3): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J3): Termos e cota do OPS no site do EPO.
- **Para que serviria no IrRAE** (coluna K, célula K3): Completa o R para empresas europeias/asiáticas e pedidos de brasileiras no exterior.
- **Sua verificação** (coluna L, célula L3): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M3):
```text
Art. 3.1: usar e incluir os dados “in their own machine-readable databases, products and services”, e distribuí-los “as part of these products”.
Art. 4.7: “No royalties are due to the EPO from the sale or licensing by users of products” feitos com dados do OPS.

Cadastro	Obrigatório, mesmo para testes
Gratuito	Até 4 GB por semana (segunda 00h a domingo 24h, horário GMT)
Acima disso	Assinatura anual de € 2.800, valor de 2025 na loja da EPO
Velocidade	Cerca de 1 Mbit/s, ~10 buscas por minuto por IP, 1 requisição por segundo em consultas de família
Horário recomendado para robôs	19h às 07h GMT ou fins de semana
Base completa	O OPS “is not designed to deliver large amounts of data”.
```

### FA-02 · Google Patents Public Datasets (BigQuery)

- Origem: aba `Fontes adicionais`, linha 4 do Excel.
- **#** (coluna A, célula A4): 2
- **Sigla / Nome da base** (coluna B, célula B4): Google Patents Public Datasets (BigQuery)
- **Órgão / mantenedor** (coluna C, célula C4): Google + IFI CLAIMS
- **Jurisdição** (coluna D, célula D4): Internacional (EUA)
- **O que fornece** (coluna E, célula E4): Patentes globais com CPC, texto e citações, consultáveis por SQL.
- **Link / onde encontrar** (coluna F, célula F4): https://github.com/google/patents-public-data
- **Tipo de acesso** (coluna G, célula G4): BigQuery (cobra processamento)
- **Custo** (coluna H, célula H4): Custo do BigQuery
- **Status preliminar** (coluna I, célula I4): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J4): "Licensed under a Creative Commons Attribution 4.0 International License" (CC BY 4.0): uso comercial com atribuição a IFI CLAIMS e Google.
- **Para que serviria no IrRAE** (coluna K, célula K4): Classificar IA por CPC (ex.: G06N) em escala global de uma só vez.
- **Sua verificação** (coluna L, célula L4): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M4): Pesquisar melhor, entendi que pode ser muito bom mas tem liimmte de 1 Tib depois fica pago, se varresse muito por algum erro teriamos que pagar

### FA-03 · WIPO PATENTSCOPE

- Origem: aba `Fontes adicionais`, linha 5 do Excel.
- **#** (coluna A, célula A5): 3
- **Sigla / Nome da base** (coluna B, célula B5): WIPO PATENTSCOPE
- **Órgão / mantenedor** (coluna C, célula C5): WIPO / OMPI
- **Jurisdição** (coluna D, célula D5): Internacional (Suíça)
- **O que fornece** (coluna E, célula E5): Pedidos PCT e coleções nacionais; relatórios de tendência de patentes de IA.
- **Link / onde encontrar** (coluna F, célula F5): https://patentscope.wipo.int/
- **Tipo de acesso** (coluna G, célula G5): Web; serviço web por assinatura
- **Custo** (coluna H, célula H5): Gratuito (web) / pago (web service)
- **Status preliminar** (coluna I, célula I5): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J5): Termos da WIPO.
- **Para que serviria no IrRAE** (coluna K, célula K5): Validação cruzada da classificação de IA.
- **Sua verificação** (coluna L, célula L5): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M5):
```text
PATENTSCOPE tem os termos mais restritivos. O banco gratuito é só para consulta manual: automação, download em massa e scraping são proibidos, e até o deep link pede autorização. Para usar no produto, é preciso comprar os dados PCT. Os relatórios da OMPI (WIPO), como o de IA generativa, são outra história: CC BY 4.0, liberados com atribuição.

Nao enxergo o porque de usar atualment
```

### FA-04 · OpenAlex

- Origem: aba `Fontes adicionais`, linha 6 do Excel.
- **#** (coluna A, célula A6): 4
- **Sigla / Nome da base** (coluna B, célula B6): OpenAlex
- **Órgão / mantenedor** (coluna C, célula C6): OurResearch
- **Jurisdição** (coluna D, célula D6): Internacional (EUA)
- **O que fornece** (coluna E, célula E6): Publicações científicas por instituição (inclui empresas: Google, Meta, NVIDIA...).
- **Link / onde encontrar** (coluna F, célula F6): https://openalex.org/  |  API: https://help.openalex.org/api/
- **Tipo de acesso** (coluna G, célula G6): API REST (sem chave para começar; chave gratuita aumenta cota; excedente pago)
- **Custo** (coluna H, célula H6): Gratuito / pago por uso
- **Status preliminar** (coluna I, célula I6): Livre
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J6): "All data is CC0" — sem restrição de licença.
- **Para que serviria no IrRAE** (coluna K, célula K6): Novo sinal de P&D em IA (papers por empresa), complementar às patentes no pilar Prospectivo.
- **Sua verificação** (coluna L, célula L6): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M6):
```text
OpenAlex: uso gratuito

O OpenAlex é um catálogo aberto de publicações científicas. Os dados estão sob licença CC0 (domínio público), então podemos usá-los comercialmente sem pedir autorização. A atribuição não é obrigatória, mas vamos exibir “Fonte: OpenAlex” por boa prática.

Desde fevereiro de 2026, a API exige uma chave, que é gratuita. Cada chave tem uma cota diária de US$ 1, renovada à meia-noite UTC. Na prática, isso dá cerca de 10 mil consultas de filtro ou agrupamento por dia, e as consultas por ID ou DOI são ilimitadas. Se a cota acabar, a API retorna erro 429 e nada é cobrado. Só há cobrança se colocarmos saldo pré-pago.

Para volumes maiores, a base completa pode ser baixada de graça, sem conta nem chave, num bucket público da AWS (s3://openalex) e processada localmente.

Decisão para o protótipo: usar a API com chave gratuita. Se o volume crescer, migrar para o snapshot. Em nenhum dos casos há custo.

Cuidados: não republicar resumos nem textos completos dos artigos, porque podem ter direitos das editoras, e trabalhar com dados agregados por instituição, sem expor nomes de autores (LGPD).
```

### FA-05 · Kenneth French Data Library

- Origem: aba `Fontes adicionais`, linha 7 do Excel.
- **#** (coluna A, célula A7): 5
- **Sigla / Nome da base** (coluna B, célula B7): Kenneth French Data Library
- **Órgão / mantenedor** (coluna C, célula C7): Dartmouth (Tuck) – K. French
- **Jurisdição** (coluna D, célula D7): EUA
- **O que fornece** (coluna E, célula E7): Retornos diários de carteiras setoriais (ex.: 49 indústrias) e fatores.
- **Link / onde encontrar** (coluna F, célula F7): https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- **Tipo de acesso** (coluna G, célula G7): Download (CSV)
- **Custo** (coluna H, célula H7): Gratuito
- **Status preliminar** (coluna I, célula I7): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J7): Não há licença comercial explícita no site — confirmar antes de uso comercial.
- **Para que serviria no IrRAE** (coluna K, célula K7): Fator do 'setor oficial' na auditoria por retornos sem pagar índice setorial.
- **Sua verificação** (coluna L, célula L7): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M7):
```text
Estudar, testar modelos, calibrar a engine internamente. NEFIN, da FEA-USP faz isso no brasil

nao uso comercial
```

### FA-06 · SEC Form 13F Data Sets

- Origem: aba `Fontes adicionais`, linha 8 do Excel.
- **#** (coluna A, célula A8): 6
- **Sigla / Nome da base** (coluna B, célula B8): SEC Form 13F Data Sets
- **Órgão / mantenedor** (coluna C, célula C8): U.S. SEC (DERA)
- **Jurisdição** (coluna D, célula D8): EUA
- **O que fornece** (coluna E, célula E8): Carteiras trimestrais de gestores institucionais nos EUA.
- **Link / onde encontrar** (coluna F, célula F8): Onde achar: sec.gov → Data & Research → Form 13F Data Sets
- **Tipo de acesso** (coluna G, célula G8): Download em lote
- **Custo** (coluna H, célula H8): Gratuito
- **Status preliminar** (coluna I, célula I8): Livre com condições
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J8): Mesma política da SEC.
- **Para que serviria no IrRAE** (coluna K, célula K8): Testar o modelo em carteiras reais de gestores (casos de uso e validação).
- **Sua verificação** (coluna L, célula L8): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M8):
```text
✅ Use o 13F normalmente, mas não exiba o CUSIP ao usuário. Mostre o nome do emissor e o ticker.
✅ Faça o mapeamento CUSIP → ticker só para os ativos que importam, por exemplo os ADRs brasileiros, que são poucas dezenas e podem ser mapeados manualmente.
❌ Não monte nem publique uma base mestre de CUSIPs.

Período	Jul/2013 a ago/2026
Atualização	Trimestral, logo após os prazos do 13F
Formato	ZIP com tabelas “achatadas” extraídas do XML (definições no README em PDF)
Qualidade	“Without change from the ‘as-filed’ submissions”. A SEC “cannot guarantee the accuracy”
Acesso automatizado	No máximo 10 requisições por segundo no total. Declare um User-Agent com nome da empresa e e-mail, ou o IP pode ser bloqueado
```

### FA-07 · filings.xbrl.org (ESEF)

- Origem: aba `Fontes adicionais`, linha 9 do Excel.
- **#** (coluna A, célula A9): 7
- **Sigla / Nome da base** (coluna B, célula B9): filings.xbrl.org (ESEF)
- **Órgão / mantenedor** (coluna C, célula C9): XBRL International
- **Jurisdição** (coluna D, célula D9): Internacional (Europa)
- **O que fornece** (coluna E, célula E9): Relatórios anuais XBRL de empresas europeias (ESEF), ex.: ASML, SAP.
- **Link / onde encontrar** (coluna F, célula F9): https://filings.xbrl.org/
- **Tipo de acesso** (coluna G, célula G9): Web + API
- **Custo** (coluna H, célula H9): Gratuito
- **Status preliminar** (coluna I, célula I9): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J9): Verificar termos do repositório.
- **Para que serviria no IrRAE** (coluna K, célula K9): Estender o A/Ir para empresas europeias da cadeia de IA.
- **Sua verificação** (coluna L, célula L9): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M9):
```text
API

Em https://filings.xbrl.org/api/filings, no padrão JSON:API, sem chave e sem limite de taxa documentado. A documentação ainda é parcial.
Há um pacote Python da comunidade, xbrl-filings-api.
Na prática, para o Sagital
Uso	Situação
Extrair números dos balanços (receita, lucro, dívida) via XBRL-JSON	✅ Sem restrição declarada. Números financeiros são fatos
Exibir indicadores calculados (margem, ROE, crescimento)	✅ Cite “Fonte: filings.xbrl.org / relatório ESEF da empresa”
```

### FA-08 · Taxonomia US-GAAP (FASB/SEC)

- Origem: aba `Fontes adicionais`, linha 10 do Excel.
- **#** (coluna A, célula A10): 8
- **Sigla / Nome da base** (coluna B, célula B10): Taxonomia US-GAAP (FASB/SEC)
- **Órgão / mantenedor** (coluna C, célula C10): FASB / SEC
- **Jurisdição** (coluna D, célula D10): EUA
- **O que fornece** (coluna E, célula E10): Dicionário oficial das tags XBRL (nomes, definições, dimensões).
- **Link / onde encontrar** (coluna F, célula F10): https://xbrl.fasb.org/  |  https://www.sec.gov/data-research/standard-taxonomies
- **Tipo de acesso** (coluna G, célula G10): Download
- **Custo** (coluna H, célula H10): Gratuito
- **Status preliminar** (coluna I, célula I10): A verificar
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J10): Taxonomia publicada pelo FASB; verificar termos.
- **Para que serviria no IrRAE** (coluna K, célula K10): Referência para o desenvolvedor mapear tags (capex, RPO, segmentos, clientes).
- **Sua verificação** (coluna L, célula L10): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M10): Por enquanto nao sera usado, achei restritivo

### FA-09 · Wikidata

- Origem: aba `Fontes adicionais`, linha 11 do Excel.
- **#** (coluna A, célula A11): 9
- **Sigla / Nome da base** (coluna B, célula B11): Wikidata
- **Órgão / mantenedor** (coluna C, célula C11): Wikimedia Foundation
- **Jurisdição** (coluna D, célula D11): Internacional
- **O que fornece** (coluna E, célula E11): Relações entre empresas (subsidiárias, aquisições), identificadores cruzados.
- **Link / onde encontrar** (coluna F, célula F11): https://www.wikidata.org/  |  SPARQL: https://query.wikidata.org/
- **Tipo de acesso** (coluna G, célula G11): API/SPARQL sem chave
- **Custo** (coluna H, célula H11): Gratuito
- **Status preliminar** (coluna I, célula I11): Livre
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J11): Dados em CC0.
- **Para que serviria no IrRAE** (coluna K, célula K11): Apoio para titular → empresa; confiabilidade média, sempre conferir com GLEIF/Exhibit 21.
- **Sua verificação** (coluna L, célula L11): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M11):
```text
Regra	Detalhe
User-Agent	Obrigatório e descritivo, com contato. A política diz: “Scripts should use an informative User-Agent string with contact information, or they may be IP-blocked without notice”. Ex.: SagitalApp/0.1 (contato@seudominio.com)
SPARQL (query.wikidata.org)	Consultas com tempo limite de cerca de 60 s e cota de uso por cliente. Não consegui abrir a documentação de limites para confirmar os números exatos; consulte o manual do Query Service
Volume grande	Use os dumps completos (JSON ou RDF) em vez de milhares de consultas SPARQL


Cuidados de qualidade
Pode estar errado ou desatualizado, inclusive por vandalismo. Por exemplo, um ticker antigo (ELET3 em vez de AXIA3) ou uma aquisição não registrada.
Use como referência cruzada, não como fonte oficial. CNPJ e participações societárias devem ser confirmados com a CVM (FRE, formulário de referência) ou a Receita.
Cobertura desigual: grandes empresas têm muitos dados; small caps brasileiras podem ter poucos ou nenhum.
Pessoas (CEOs, fundadores) também estão lá. Mantenha o produto em dados de empresa (LGPD).
```

### FA-10 · sec-api.io (intermediário comercial)

- Origem: aba `Fontes adicionais`, linha 12 do Excel.
- **#** (coluna A, célula A12): 10
- **Sigla / Nome da base** (coluna B, célula B12): sec-api.io (intermediário comercial)
- **Órgão / mantenedor** (coluna C, célula C12): Empresa privada
- **Jurisdição** (coluna D, célula D12): EUA
- **O que fornece** (coluna E, célula E12): Acesso já estruturado a EDGAR (N-PORT, texto, segmentos).
- **Link / onde encontrar** (coluna F, célula F12): https://sec-api.io/
- **Tipo de acesso** (coluna G, célula G12): API (chave)
- **Custo** (coluna H, célula H12): Pago
- **Status preliminar** (coluna I, célula I12): Licença/contrato necessário
- **Validade jurídica (leitura preliminar — confirmar)** (coluna J, célula J12): Termos comerciais do fornecedor.
- **Para que serviria no IrRAE** (coluna K, célula K12): Atalho de engenharia; os dados originais são gratuitos na SEC.
- **Sua verificação** (coluna L, célula L12): VALIDADO
- **Notas da sua pesquisa** (coluna M, célula M12): Desnecessario por agora

## Seção 4 — Aba `Base legal` (15 normas/licenças, transcrição integral)

Colunas da aba, na ordem do Excel: A = `Norma / licença` · B = `Jurisdição` · C = `O que diz (resumo)` · D = `Onde ler` · E = `Afeta quais fontes`

### BL-01 · 17 U.S.C. §105

- Origem: aba `Base legal`, linha 2 do Excel.
- **Norma / licença** (coluna A, célula A2): 17 U.S.C. §105
- **Jurisdição** (coluna B, célula B2): EUA
- **O que diz (resumo)** (coluna C, célula C2): Obras do governo federal dos EUA não têm proteção de direito autoral.
- **Onde ler** (coluna D, célula D2): https://www.law.cornell.edu/uscode/text/17/105
- **Afeta quais fontes** (coluna E, célula E2): SEC, USPTO, Census (conteúdo produzido pelo governo)

### BL-02 · Política de informação pública da SEC

- Origem: aba `Base legal`, linha 3 do Excel.
- **Norma / licença** (coluna A, célula A3): Política de informação pública da SEC
- **Jurisdição** (coluna B, célula B3): EUA
- **O que diz (resumo)** (coluna C, célula C3): Informação em sec.gov é pública e pode ser copiada e redistribuída sem permissão; marcas e logos SEC/EDGAR não.
- **Onde ler** (coluna D, célula D3): https://www.sec.gov/about/privacy-information
- **Afeta quais fontes** (coluna E, célula E3): Todas as fontes SEC

### BL-03 · SEC Fair Access (acesso automatizado)

- Origem: aba `Base legal`, linha 4 do Excel.
- **Norma / licença** (coluna A, célula A4): SEC Fair Access (acesso automatizado)
- **Jurisdição** (coluna B, célula B4): EUA
- **O que diz (resumo)** (coluna C, célula C4): Máximo 10 requisições/s, User-Agent com nome e e-mail, baixar só o necessário.
- **Onde ler** (coluna D, célula D4): https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- **Afeta quais fontes** (coluna E, célula E4): Todas as fontes SEC

### BL-04 · Termos de uso da USPTO

- Origem: aba `Base legal`, linha 5 do Excel.
- **Norma / licença** (coluna A, célula A5): Termos de uso da USPTO
- **Jurisdição** (coluna B, célula B5): EUA
- **O que diz (resumo)** (coluna C, célula C5): Conteúdo do governo em domínio público com atribuição; proibido bulk pelas interfaces web; bloqueio por acesso excessivo.
- **Onde ler** (coluna D, célula D5): https://www.uspto.gov/terms-use-uspto-websites
- **Afeta quais fontes** (coluna E, célula E5): AIPD, ODP, PatentsView, Assignment

### BL-05 · CC0 1.0

- Origem: aba `Base legal`, linha 6 do Excel.
- **Norma / licença** (coluna A, célula A6): CC0 1.0
- **Jurisdição** (coluna B, célula B6): Internacional
- **O que diz (resumo)** (coluna C, célula C6): Dedicação ao domínio público: uso comercial livre, sem atribuição obrigatória.
- **Onde ler** (coluna D, célula D6): https://creativecommons.org/publicdomain/zero/1.0/
- **Afeta quais fontes** (coluna E, célula E6): GLEIF, OpenAlex, Wikidata

### BL-06 · CC BY 4.0

- Origem: aba `Base legal`, linha 7 do Excel.
- **Norma / licença** (coluna A, célula A7): CC BY 4.0
- **Jurisdição** (coluna B, célula B7): Internacional
- **O que diz (resumo)** (coluna C, célula C7): Uso comercial e derivações permitidos com atribuição.
- **Onde ler** (coluna D, célula D7): https://creativecommons.org/licenses/by/4.0/
- **Afeta quais fontes** (coluna E, célula E7): Google Patents Public Datasets

### BL-07 · CC BY-ND 3.0

- Origem: aba `Base legal`, linha 8 do Excel.
- **Norma / licença** (coluna A, célula A8): CC BY-ND 3.0
- **Jurisdição** (coluna B, célula B8): Internacional
- **O que diz (resumo)** (coluna C, célula C8): Permite redistribuir com atribuição, mas proíbe obras derivadas — ponto de atenção.
- **Onde ler** (coluna D, célula D8): https://creativecommons.org/licenses/by-nd/3.0/
- **Afeta quais fontes** (coluna E, célula E8): Site do INPI (confirmar se vale para os dados)

### BL-08 · MIT (padrão FIGI)

- Origem: aba `Base legal`, linha 9 do Excel.
- **Norma / licença** (coluna A, célula A9): MIT (padrão FIGI)
- **Jurisdição** (coluna B, célula B9): Internacional
- **O que diz (resumo)** (coluna C, célula C9): Uso, cópia e redistribuição livres, mantendo o aviso de licença.
- **Onde ler** (coluna D, célula D9): https://www.openfigi.com/about/faq
- **Afeta quais fontes** (coluna E, célula E9): OpenFIGI

### BL-09 · ODbL 1.0 (Open Database License)

- Origem: aba `Base legal`, linha 10 do Excel.
- **Norma / licença** (coluna A, célula A10): ODbL 1.0 (Open Database License)
- **Jurisdição** (coluna B, célula B10): Internacional
- **O que diz (resumo)** (coluna C, célula C10): Uso comercial permitido; atribuição; bases derivadas usadas publicamente devem manter a ODbL (share-alike); manter aberta a versão derivada se redistribuída.
- **Onde ler** (coluna D, célula D10): https://opendatacommons.org/licenses/odbl/
- **Afeta quais fontes** (coluna E, célula E10): Portal Dados Abertos CVM

### BL-10 · Lei 12.527/2011 (LAI)

- Origem: aba `Base legal`, linha 11 do Excel.
- **Norma / licença** (coluna A, célula A11): Lei 12.527/2011 (LAI)
- **Jurisdição** (coluna B, célula B11): Brasil
- **O que diz (resumo)** (coluna C, célula C11): Acesso à informação pública; base da transparência ativa dos órgãos.
- **Onde ler** (coluna D, célula D11): https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm
- **Afeta quais fontes** (coluna E, célula E11): CVM, Receita, INPI, IBGE, BCB

### BL-11 · Decreto 8.777/2016 (Política de Dados Abertos)

- Origem: aba `Base legal`, linha 12 do Excel.
- **Norma / licença** (coluna A, célula A12): Decreto 8.777/2016 (Política de Dados Abertos)
- **Jurisdição** (coluna B, célula B12): Brasil
- **O que diz (resumo)** (coluna C, célula C12): Institui a política de dados abertos do Executivo federal e os planos de dados abertos.
- **Onde ler** (coluna D, célula D12): https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2016/decreto/d8777.htm
- **Afeta quais fontes** (coluna E, célula E12): Receita, INPI, IBGE, BCB (a CVM é autarquia federal)

### BL-12 · Lei 13.709/2018 (LGPD)

- Origem: aba `Base legal`, linha 13 do Excel.
- **Norma / licença** (coluna A, célula A13): Lei 13.709/2018 (LGPD)
- **Jurisdição** (coluna B, célula B13): Brasil
- **O que diz (resumo)** (coluna C, célula C13): Tratamento de dados pessoais, inclusive os publicamente acessíveis, exige finalidade, necessidade e boa-fé.
- **Onde ler** (coluna D, célula D13): https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- **Afeta quais fontes** (coluna E, célula E13): Receita CNPJ (QSA), qualquer base com pessoas físicas

### BL-13 · Lei 9.610/1998, art. 7º, XIII

- Origem: aba `Base legal`, linha 14 do Excel.
- **Norma / licença** (coluna A, célula A14): Lei 9.610/1998, art. 7º, XIII
- **Jurisdição** (coluna B, célula B14): Brasil
- **O que diz (resumo)** (coluna C, célula C14): Bases de dados que constituem criação intelectual são protegidas por direito autoral.
- **Onde ler** (coluna D, célula D14): https://www.planalto.gov.br/ccivil_03/leis/l9610.htm
- **Afeta quais fontes** (coluna E, célula E14): Bases privadas (B3, ANBIMA, fornecedores de preço)

### BL-14 · Política Comercial de Market Data B3 (v3.0.4)

- Origem: aba `Base legal`, linha 15 do Excel.
- **Norma / licença** (coluna A, célula A15): Política Comercial de Market Data B3 (v3.0.4)
- **Jurisdição** (coluna B, célula B15): Brasil
- **O que diz (resumo)** (coluna C, célula C15): Históricos e fim de dia: distribuição livre; criação de índices/dados derivados: exige autorização; non-display: licença.
- **Onde ler** (coluna D, célula D15): https://www.b3.com.br/data/files/EF/77/94/75/0AB929106EEC8429AC094EA8/Market%20Data%20Commercial%20Policy%20v3.0.4.1.pdf
- **Afeta quais fontes** (coluna E, célula E15): COTAHIST, índices B3, BDRs/ETFs

### BL-15 · Licença CUSIP (CGS)

- Origem: aba `Base legal`, linha 16 do Excel.
- **Norma / licença** (coluna A, célula A16): Licença CUSIP (CGS)
- **Jurisdição** (coluna B, célula B16): EUA
- **O que diz (resumo)** (coluna C, célula C16): Uso de base de identificadores CUSIP em produtos pode exigir licença e taxas.
- **Onde ler** (coluna D, célula D16): https://www.cusip.com/services/license-fees.html
- **Afeta quais fontes** (coluna E, célula E16): N-PORT (campo CUSIP)

## Seção 5 — [REVISOR] Decisão de uso por fonte (resumo derivado das notas — NÃO está no Excel)

> Esta tabela é uma **interpretação** das colunas `Notas da sua pesquisa` / `Observações` de cada ficha, feita para evitar que o leitor tenha de deduzir a decisão. A fonte de verdade continua sendo a ficha (Seções 2 e 3). Em caso de divergência entre esta tabela e a ficha, **vale a ficha**, e a divergência deve ser levada ao dono do projeto.
>
> Legenda: **USAR** = usar na v1 respeitando as condições · **USAR (restrito)** = usar só para a finalidade indicada · **NÃO USAR NA V1** = decisão explícita do dono de não usar agora · **SÓ MANUAL** = sem automação · **PENDENTE** = dono ainda não decidiu · **INDEFINIDO** = notas não deixam a decisão clara (perguntar ao dono).

| ID | Fonte | Decisão | Condições principais | Base (células) |
|---|---|---|---|---|
| FP-01 | SEC EDGAR – Archives | USAR | ≤10 req/s; User-Agent com nome + e-mail; não usar "SEC"/logo EDGAR nem sugerir vínculo com a SEC | K3, O3 |
| FP-02 | SEC EDGAR APIs (data.sec.gov) | USAR | Mesmas da FP-01; bulk noturno (~3:00 ET) | K4, O4 |
| FP-03 | SEC FSN | USAR | Mesmas da FP-01; previsto no código v1, ainda não rodado com dados reais | K5, M5 |
| FP-04 | SEC Financial Statement Data Sets | USAR | Alternativa leve à FP-03 quando não precisar de segmentos | M6 |
| FP-05 | XBRL / Inline XBRL (R-files) | USAR | Conferir soma dos segmentos contra o consolidado | M7 |
| FP-06 | EDGAR Full-Text Search (EFTS) | USAR (restrito) | Só triagem; endpoint JSON não oficial (pode mudar); exemplo de código com User-Agent em O8 | K8, M8, O8 |
| FP-07 | SEC company_tickers.json | USAR | **CIK = chave primária; ticker só atributo**; arquivo sem garantia de exatidão | M9, O9 |
| FP-08 | SEC SIC Code List | USAR | Não usar GICS (proprietário MSCI/S&P) | M10, O10 |
| FP-09 | SEC N-PORT Data Sets | PENDENTE | `Sua verificação` = Pendente. Campo CUSIP/ISIN US sujeito à licença CGS (ver FP-18) | N11, O11 |
| FP-10 | SEC N-PORT XML | PENDENTE | Idem FP-09 | N12, O12 |
| FP-11 | SEC N-CEN | USAR | Confirmar tipo do fundo antes do look-through | M13 |
| FP-12 | USPTO AIPD | USAR | Creditar USPTO; citar o paper do AIPD na metodologia; sem logo/selo; download via bulk | O14 |
| FP-13 | USPTO ODP – APIs | USAR | Conta USPTO.gov + ID.me; 1 requisição por vez por chave; bulk para volume; só metadados | O15 |
| FP-14 | PatentsView | USAR (restrito) | Baixar **só tabelas de assignees** (não importar inventores); atribuição CC BY 4.0 + link + aviso de modificação; LGPD | O16 |
| FP-15 | USPTO Patent Assignment Dataset | USAR | Histórico de cessões **até 2023**; citar Marco et al. (2015); só PJ (descartar PF na ingestão) | O17, O18 |
| FP-15b | Patent Assignment XML | USAR | Cessões **a partir de 2024**, importação mensal; parsing do XML separando cessão/fusão/mudança de nome de garantia/licença/ônus; checar junção 2023/2024; alertar falhas | O18 |
| FP-16 | GLEIF | USAR | CC0 | K19 |
| FP-17 | OpenFIGI | USAR | Respeitar limites de requisição (tabela em O20) | K20, O20 |
| FP-18 | CUSIP | NÃO USAR | Não usar nem armazenar CUSIP; usar FIGI/LEI/identificador interno. Ver conflito sobre ISIN na Seção 6, item 9 | O21 |
| FP-19 | Preços diários EUA (licenciados) | NÃO USAR NA V1 | Modelo roda sem preços; retornos só auditoria | M22, O22 |
| FP-20 | NAICS | USAR (opcional) | Se usar a API do Census, exibir o aviso exigido (texto em O23) | M23, O23 |
| FP-21 | CVM DFP | USAR | ODbL: atribuição; base derivada publicada mantém ODbL | K24 |
| FP-22 | CVM ITR | USAR | ODbL | K25 |
| FP-23 | CVM FRE | USAR | ODbL | K26 |
| FP-24 | CVM Cadastro de Companhias | USAR | ODbL; chave CVM ↔ CNPJ ↔ ticker | K27, M27 |
| FP-25 | CVM CDA | USAR | ODbL; posições confidenciais = "não coberto"; ETFs nos arquivos `cda_fiim_*` / `cda_fie_*` | M28, O28 |
| FP-26 | CVM Cadastro de Fundos | USAR | ODbL; estrutura pós-Res. CVM 175 (fundo/classe/subclasse) | M29, O29 |
| FP-27 | CVM RAD / Empresas.NET | INDEFINIDO | `Status preliminar` = A verificar; nota: "Nao achei nada sobre comercial e API". Sugestão do revisor: só consulta manual até confirmar | J30, K30, O30 |
| FP-28 | B3 COTAHIST | NÃO USAR NA V1 | "Por enquanto nao e necessario os dados historicos" | O31 |
| FP-29 | B3 BDRs e ETFs | NÃO USAR (dados B3) | ETFs: usar CDA da CVM (FP-25). BDRs: teste com 20 tickers mapeando o lastro pelo OpenFIGI (FP-17) | O32 |
| FP-30 | B3 Composição de índices | NÃO USAR NA V1 | CVM cobre pesos (1 mês de atraso); preços vêm do usuário | O33 |
| FP-31 | ISIN – Brasil | USAR (restrito) | Armazenar **o ISIN fornecido pelo usuário no CSV**; se vier ticker sem ISIN, criar código interno; sufixo `F` (ex.: BBDC3F) = mercado fracionário do mesmo papel, não outro ativo | O34 |
| FP-32 | INPI Dados Abertos | USAR | Sem logo do INPI; não editar/copiar textos do site; **apagar CPF e dados de PF na ingestão** | O35 |
| FP-33 | INPI pePI | SÓ MANUAL | Não aceita robôs | O36 |
| FP-34 | Receita – CNPJ | USAR (restrito) | Filtrar pelo universo (CVM/fundos); excluir empresário individual/MEI; não guardar Sócios, e-mail, telefone; crédito à Receita | O37 |
| FP-35 | IBGE CNAE | USAR | Baixar a estrutura uma vez e guardar local; crédito IBGE/CONCLA | O38 |
| FP-36 | BCB SGS / PTAX | USAR | PTAX do USD livre; outras moedas com cautela; repassar aviso da API Olinda | O39 |
| FP-37 | ANBIMA | NÃO USAR | CVM cobre os fundos (ANBIMA só agrega classificação/índices próprios) | M40, O40 |
| FA-01 | EPO OPS | INDEFINIDO (termos permitem) | Termos permitem uso em produto (art. 3.1, 4.7); 4 GB/semana grátis; uso na v1 não decidido explicitamente | M3 |
| FA-02 | Google Patents (BigQuery) | PENDENTE | "Pesquisar melhor"; risco de custo acima de 1 TiB/mês | M4 |
| FA-03 | WIPO PATENTSCOPE | NÃO USAR | "Nao enxergo o porque de usar atualment" | M5 |
| FA-04 | OpenAlex | USAR | API com chave gratuita; snapshot se crescer; não republicar resumos/textos; sem nomes de autores | M6 |
| FA-05 | Kenneth French Data Library | NÃO USAR (comercial) | Só estudo/calibração interna | M7 |
| FA-06 | SEC 13F | USAR | Não exibir CUSIP; mapear CUSIP→ticker só para poucos ativos; não montar base mestre de CUSIPs | M8 |
| FA-07 | filings.xbrl.org | USAR | Citar "filings.xbrl.org / relatório ESEF da empresa" | M9 |
| FA-08 | Taxonomia US-GAAP (FASB) | NÃO USAR por enquanto | "achei restritivo" — ver Seção 6, item 12 | M10 |
| FA-09 | Wikidata | USAR (restrito) | Só referência cruzada; conferir com CVM/GLEIF/Exhibit 21; User-Agent obrigatório | K11, M11 |
| FA-10 | sec-api.io | NÃO USAR | "Desnecessario por agora" | M12 |

## Seção 6 — [REVISOR] Inconsistências e ambiguidades encontradas no Excel (o conteúdo das fichas NÃO foi alterado)

1. **Linha sem número (`FP-15b`, aba `Fontes principais`, linha 18).** A coluna `#` (A18) e `Órgão / mantenedor` (C18) estão vazias, e o nome (B18) começa com um caractere TAB. Leitura do revisor: é um sub-item da `FP-15` (mesmo tema, links em data.uspto.gov) mantido pela USPTO. A nota O18 explica a divisão: FP-15 até 2023, FP-15b de 2024 em diante.
2. **`FP-26`, célula K29:** o texto termina com `+K29` ("ODbL (ver DFP).+K29") — artefato de digitação; o conteúdo pretendido é "ODbL (ver DFP).".
3. **`FP-32`, célula H35 (`Tipo de acesso`):** repete os links da coluna G35 em vez de descrever o tipo de acesso. Pelas demais fichas da CVM/Receita, o tipo de acesso provável é "Download em lote (CSV/ZIP)" — confirmar.
4. **`FP-27`, célula G30 (`Link / onde encontrar`):** contém só um espaço em branco (sem link). Os termos citados estão em L30.
5. **`FP-35`, célula O38:** o bloco que começa em "Dicas de implementação:" e termina em "confirme a versão vigente no site." aparece **duas vezes seguidas** (duplicação por colagem). O conteúdo das duas cópias é idêntico; ambas foram transcritas.
6. **Hiperlinks embutidos divergentes do texto visível:**
   - G29 (`FP-26`): o hiperlink embutido é inválido (inclui o texto "(ou busca 'cadastro de fundos' no portal)" dentro da URL). Use a URL do texto: `https://dados.cvm.gov.br/dataset/fi-cad`.
   - O9 (`FP-07`): o hiperlink embutido aponta para `https://www.sec.gov/about/webmaster-frequently-asked-questions` sem a âncora; o texto traz a URL completa com `#ticker-cik`.
7. **Coluna `Sua verificação` com valor fora da lista:** 36 de 38 linhas de `Fontes principais` e todas as 10 de `Fontes adicionais` têm `VALIDADO`, que não está na lista suspensa (`Pendente, Aprovado, Aprovado com condições, Reprovado`). Ver Seção 0, item 5: `VALIDADO` ≠ "aprovado para uso".
8. **`Status preliminar` desatualizado em relação às notas.** Exemplos: FP-32 (INPI), FP-35 (IBGE) e FP-36 (BCB) continuam "A verificar", mas as notas já definem o uso. As contagens da aba `Leia-me` (B15–B18) refletem esse status preliminar. Regra: Seção 0, item 4.
9. **Conflito sobre armazenar ISIN.** O21 (`FP-18`) diz: "CUSIP E ISIN POR SEREM PAGOS NAO DEVERIAM NEM SER ARMAZENADOS NA BASE DO TRACKER". O34 (`FP-31`) manda armazenar internamente o ISIN brasileiro fornecido pelo usuário. Leitura do revisor para conciliar (confirmar com o dono): o ISIN de títulos dos EUA e do Canadá (prefixos `US`/`CA`) contém o próprio CUSIP dentro do código, por isso cai na restrição da CGS (ver também O11 e O12: "campo CUSIP/ISIN US sujeito à licença CGS"); ISINs brasileiros (prefixo `BR`) são atribuídos pela B3 e não contêm CUSIP. Regra proposta: **não armazenar CUSIP nem ISIN baseado em CUSIP (ex.: `US…`, `CA…`); armazenar ISIN `BR…` quando vier do CSV do usuário**.
10. **CDI como benchmark (O33, `FP-30`).** A nota diz que "CDI, Selic e IPCA também são públicas". Informação levantada depois, na conversa com o revisor: a Taxa DI/CDI é **apurada e divulgada pela B3** (o SGS do BCB, série 12, apenas a republica), então pode estar sujeita às regras da B3; Selic (BCB, séries SGS 11/432) e IPCA (IBGE, republicado no SGS série 433) não têm esse problema. Até a B3 confirmar, preferir Selic como benchmark de renda fixa. Fonte: B3, "Taxa DI" (https://borainvestir.b3.com.br/glossario/taxa-di/).
11. **Licença do PatentsView (`FP-14`).** K16 diz "Mesmos termos da USPTO"; O16 (posterior) diz que a licença é CC BY 4.0 e lista os itens de atribuição. Vale O16 (Seção 0, item 4): aplicar atribuição CC BY 4.0.
12. **Taxonomia US-GAAP (`FA-08`) × tags XBRL usadas na `FP-02`/`FP-03`/`FP-05`.** A decisão "Por enquanto nao sera usado" (M10) refere-se à taxonomia publicada pelo FASB (arquivos, rótulos e definições). As fichas FP-02 (F4) e FP-03 usam nomes de tags XBRL (ex.: `PaymentsToAcquirePropertyPlantAndEquipment`, `RevenueRemainingPerformanceObligation`) que vêm **dentro dos dados da SEC**. Leitura do revisor (confirmar com o dono): usar esses nomes como chaves técnicas continua permitido; o que não se faz é baixar/exibir os arquivos, rótulos ou definições do FASB. Atenção: a API `companyfacts` da SEC (FP-02) traz os campos `label` e `description`, que são textos da taxonomia FASB — não exibi-los; usar rótulos próprios em português.
13. **Política de Market Data B3 citada (K31, L31, BL-15) é a v3.0.4 (2024).** Uma nova Política de Market Data da B3 entrou em vigor em 01/01/2026 (Ofício Circular B3 104/2025-PRE), com a "Política de Consumo de Market Data" e a "Política Comercial de Market Data 2026". Os preços citados em O31 já são da versão 2026. Como as fontes B3 estão marcadas "não usar na v1", isso não afeta o protótipo, mas a referência legal deve ser atualizada antes de qualquer uso de dados B3.
14. **Pergunta já respondida dentro do próprio Excel.** O32 (`FP-29`) pede "Confirmem se os ETFs estão no CDA". O28 (`FP-25`) responde: as aplicações dos fundos de índice (FIIM) desde a competência 06/2018 estão em `cda_fiim_AAAAMM.csv` (renomeados para `cda_fie_AAAAMM.csv` a partir de 15/11/2025), com as confidenciais em `cda_fiim_CONFID_AAAAMM.csv` / `cda_fie_CONFID_AAAAMM.csv`.
15. **Placeholders a substituir.** O8 (`FP-06`) usa o User-Agent de exemplo `"MinhaEmpresa Ltda contato@minhaempresa.com.br"`; M11 (`FA-09`) usa `SagitalApp/0.1 (contato@seudominio.com)`. Ambos precisam ser trocados pelo nome e e-mail reais do projeto antes de qualquer acesso automatizado.
16. **Formatação visual do Excel (sem conteúdo informativo adicional):** cabeçalhos em azul-escuro; colunas `Sua verificação`/`Notas da sua pesquisa` em amarelo (campos do dono); coluna `Jurisdição` das linhas brasileiras (FP-21 a FP-37) com fundo verde-claro; N8 (`FP-06`) com fundo verde; N11 e N12 (`Pendente`) em amarelo. Formatação condicional colore a coluna de `Status preliminar` conforme os 4 valores possíveis. Nenhuma linha ou coluna oculta; nenhum comentário de célula; nenhum nome definido.

## Seção 7 — [REVISOR] Verificação de integridade

Este arquivo foi gerado por script a partir do Excel e depois conferido por um segundo script que relê o Excel e compara **cada célula não vazia** (texto exato, incluindo quebras de linha, tabulações e espaços), **cada hiperlink embutido**, **cada fórmula e seu valor calculado** e **as listas de validação** com o que está escrito aqui. Resultado da conferência (10/10/2026): **835 de 835 células não vazias idênticas ao Excel** (caractere por caractere), 12 células vazias dentro das fichas confirmadas como vazias, 9 hiperlinks embutidos idênticos, 10 fórmulas com o valor calculado conferido, 2 listas de validação transcritas; **0 divergências**. Teste de controle do próprio verificador: numa cópia com 4 erros plantados (um acento removido, uma tabulação trocada por espaço, um link truncado e um campo apagado), o verificador acusou os 4.
