# ADR 0005: Identificação de ativos e empresas (`ativo_id` e `empresa_id`)

- **Status:** aceito no conceito em 2026-10-02. Os itens marcados *(a conferir no PR)* são regras de
  implementação para a revisão do PR.
- **Data:** 2026-10-02
- **Decisores:** Lucas (Membro 2) e M1. Decisão conjunta R-02 de `docs/decisoes_m1_irrae_v1.1.md`.
- **Substitui:** a linha "Identificador de empresa" do ADR 0003 e a regra "a chave de empresa é o ISIN" do
  `CLAUDE.md`. **Afeta:** o ADR 0002 (identificação do ativo) e a D-17 da v1.1 do IrRAE.

## Contexto

Hoje o ISIN faz dois papéis ao mesmo tempo: identifica **o que está na carteira** (uma classe de ação, um
ETF, a cota de um fundo) e **quem emitiu** (a empresa, onde ficam o setor e os temas). Isso causa dois
problemas:

1. **Classes da mesma empresa contadas como empresas diferentes (DT-3).** PETR3 e PETR4 têm ISINs diferentes e
   aparecem como duas empresas na lista. A DT-3 vence no portão P3 (23/10/2026).
2. **Licença do CUSIP (R-02).** O ISIN americano é "US" + CUSIP + dígito, e o CUSIP é licenciado pela CUSIP
   Global Services (CGS). Pela leitura do M1, a licença só é dispensável se **nenhuma parte do sistema
   guardar CUSIP ou ISIN americano**. A consulta à CGS (formulário UOSS) ainda não teve resposta.

A troca é mais barata agora: o banco ainda não existe e o front ainda não consome a API.

## Decisões

### 1. Dois identificadores

| Identificador | O que identifica | Onde é usado |
|---|---|---|
| `ativo_id` | o que está numa carteira ou dentro de um fundo | posições do usuário, composições de fundos, look-through |
| `empresa_id` | quem emitiu | classificação (setor e temas), agregação por empresa, lista de empresas da resposta |

Cada ativo do tipo ação aponta para uma empresa. Classes da mesma empresa (PETR3 e PETR4; GOOGL e GOOG)
somam na mesma empresa, e a resposta mostra o tipo e a % de cada classe. **Isso fecha a DT-3.**

### 2. Formato do `ativo_id`

| Ativo | `ativo_id` | Exemplo de formato |
|---|---|---|
| Ação, BDR ou ETF com ISIN de país da **lista permitida** | o próprio ISIN | `BR` + 9 caracteres + dígito |
| Ativo negociado nos EUA | `US:` + ticker | `US:GOOGL` |
| Fundo brasileiro (em bolsa ou não) | `CNPJ:` + 14 dígitos | `CNPJ:` + 14 dígitos |

- **Lista permitida de países do ISIN:** `BR` (ações, BDRs e ETFs da B3), `IE` e `LU` (ETFs UCITS). ISIN de
  país fora da lista **nunca é guardado**. Usar lista de permitidos, e não de proibidos, porque a fronteira
  da CGS inclui EUA, Canadá e ISINs de outros países numerados por ela; na dúvida, o sistema não guarda.
  *(a conferir no PR: países da lista)*
- **Fundos brasileiros sempre pelo CNPJ**, mesmo os negociados na B3 (FIIs, ETFs), porque a CVM identifica
  os fundos e as cotas de fundos dentro de outros fundos pelo CNPJ. O ticker e o ISIN de um fundo em bolsa
  apontam para o mesmo `CNPJ:`.

### 3. Formato do `empresa_id`

Derivado só de identificadores públicos e sem licença, na ordem de prioridade:

| Prioridade | `empresa_id` | Fonte (`docs/matriz_de_dados.md`) |
|---|---|---|
| 1 | `BR:CNPJ:` + 14 dígitos | CVM, cadastro de companhias abertas (fonte 3) |
| 2 | `US:CIK:` + 10 dígitos | SEC EDGAR (fonte 7) |
| 3 | `LEI:` + 20 caracteres | campo `lei` do N-PORT (fonte 6; D-08, sem a API do GLEIF) |

- Uma empresa brasileira com ADR na bolsa americana fica com o CNPJ.
- O mesmo código sai em qualquer máquina, sem banco nem contador central.
- Se o identificador público mudar (fusão, troca de CNPJ), cria-se um apelido; um `empresa_id` nunca é
  reaproveitado para outra empresa.
- Nos testes, só identificadores sintéticos, com prefixo `ZZ:`.

### 4. Tabela de identificadores

- **Por ativo:** `ativo_id`, ticker da B3, ticker americano, ISIN (só da lista permitida), CNPJ (fundos) e
  `empresa_id` (ações).
- **Por empresa:** `empresa_id`, nome, CNPJ, CIK e LEI.
- **CUSIP e ISIN fora da lista:** campo opcional, **desligado por padrão**. Só pode ser ligado com licença
  da CGS, por decisão conjunta.
- A ligação ticker americano → CIK depende de fontes ainda em espera (`company_tickers.json`, seção 4 de
  `docs/decisoes_m1_irrae_v1.1.md`). Até lá, uma tabela curada à mão para as empresas do escopo (D-08).

### 5. Entrada do POST /raiox

Cada posição passa a ter `identificador` e `tipo_identificador`, no lugar do campo `isin`:

| `tipo_identificador` | Validação |
|---|---|
| `isin` | formato, dígito verificador e país na lista permitida |
| `ticker_b3` | 4 letras e 1 ou 2 dígitos (ex.: PETR4, BOVA11, BDRs como AAPL34) *(a conferir no PR)* |
| `ticker_eua` | 1 a 5 letras, com classe opcional (ex.: BRK.B) *(a conferir no PR)* |
| `cnpj` | 14 dígitos e dígitos verificadores |

- **Ação americana entra só pelo ticker.** Sem guardar ISINs americanos, não há como ligar um ISIN americano
  a uma empresa. Um ISIN de país fora da lista recebe 422, com um motivo que pede o ticker.
- Identificador válido mas desconhecido continua indo para "não identificado", como hoje.
- Continua valendo a regra das mensagens de erro: nunca repetir o valor enviado.
- Os leitores de CSV (ADR 0002) já sabem a origem do arquivo: a B3 traz ticker da B3 e a Avenue traz ticker
  americano.

### 6. Ingestão

- **Composições da CVM (CDA):** um ISIN de país fora da lista (ex.: ação americana dentro de um fundo
  brasileiro) é trocado pelo ticker na ingestão, e o ISIN é descartado. Sem ticker, o ativo vai para "não
  identificado". Confirmado pelo M1.
- **N-PORT:** classes da mesma empresa consolidadas pelo LEI (D-08). O lote do IrRAE só usa o CUSIP em
  memória, como hoje, até o resultado da T-01 (R-01). Nenhuma tabela de CUSIPs é gravada no repositório
  nem no banco.

## Consequências

- **Regras:** muda a regra do `CLAUDE.md`; o ADR 0003 e o item 3 do ADR 0002 apontam para este ADR.
- **Código, em PRs pequenos e com teste primeiro:**
  1. Motor: `isin` vira `ativo_id`, e a agregação agrupa por `empresa_id`, com o tipo e a % de cada classe.
     Fecha a DT-3.
  2. Dados de exemplo: uma empresa sintética com duas classes de ações.
  3. API: a entrada nova (seção 5) e o `empresa_id` na resposta. Muda o contrato da API, mas o front ainda
     não o consome.
  4. IrRAE: a entrada da D-17 passa a usar o `ativo_id`.
- **Testes:** a maior parte da mudança é renomear `isin` para `ativo_id`. Faz parte desta decisão, não é
  para fazer teste passar.
- **`backend/CLAUDE.md`:** a regra sobre validação de identificadores muda no PR da API, junto com o código.

## Alternativas descartadas

- **Manter o ISIN e esperar a resposta da CGS:** sem custo agora, mas, se a resposta for tardia ou negativa,
  a troca fica mais cara com o banco e as telas prontos.
- **`empresa_id` opaco e sequencial:** exige um registro central (o banco), que ainda não existe, e não sai
  igual em máquinas diferentes.
- **Licenciar o CUSIP:** custo desconhecido. Continua possível depois, pelo campo opcional da seção 4.
