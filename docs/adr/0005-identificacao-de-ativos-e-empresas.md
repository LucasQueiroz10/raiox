# ADR 0005: Identificação de ativos e empresas (`ativo_id` e `empresa_id`)

- **Status:** aceito no conceito em 2026-10-02. Os itens marcados *(a conferir no PR)* são regras de
  implementação para a revisão do PR.
- **Data:** 2026-10-02. Revisado em 2026-10-04 com o resultado preliminar da T-01 (seções 2, 3, 4 e 6) e em
  2026-10-08 com o CNPJ alfanumérico (seções 2, 3 e 5) e em 2026-10-13 com o código interno da B3 e a
  raiz do ticker (seções 2 e 5).
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
3. **O N-PORT não traz ticker nem CIK (T-01 preliminar do M1).** No N-PORT do IVV (data-base 30/06/2026),
   98,99% do peso das ações tem LEI válido e o resto tem só o nome; nenhuma linha tem ticker. O CUSIP é
   dispensável para identificar as empresas, mas ligar a empresa do ETF à mesma empresa na carteira do
   usuário (que chega pelo ticker) exige uma tabela que junte LEI, CIK e ticker. É um ETF de uma gestora
   só; a T-01 oficial e a extensão (VTI, IWM, um ETF de IA e o VXUS) confirmam ou não.

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
| Fundo brasileiro (em bolsa ou não) | `CNPJ:` + CNPJ de 14 caracteres | `CNPJ:` + 12 letras ou números + 2 dígitos |
| Ação brasileira sem ISIN conhecido | `B3:` + ticker (código interno) | `B3:` + raiz de 4 caracteres + 1 ou 2 dígitos |

- **Lista permitida de países do ISIN:** `BR` (ações, BDRs e ETFs da B3), `IE` e `LU` (ETFs UCITS). ISIN de
  país fora da lista **nunca é guardado**. Usar lista de permitidos, e não de proibidos, porque a fronteira
  da CGS inclui EUA, Canadá e ISINs de outros países numerados por ela; na dúvida, o sistema não guarda.
  *(a conferir no PR: países da lista)*
- **Fundos brasileiros sempre pelo CNPJ**, mesmo os negociados na B3 (FIIs, ETFs), porque a CVM identifica
  os fundos e as cotas de fundos dentro de outros fundos pelo CNPJ. O ticker e o ISIN de um fundo em bolsa
  apontam para o mesmo `CNPJ:`.
- **Código interno da B3** (decisão de 13/10/2026, seção 5): a ação brasileira que nenhum fundo
  tem não tem ISIN em nenhuma fonte liberada (o FCA liga o ticker à companhia, mas não traz o
  ISIN; o serviço de ISIN da B3 não está liberado). Ela fica como `B3:` + ticker, ligada à
  companhia, e passa ao ISIN quando o CDA trouxer o dela. A raiz do ticker (os 4 primeiros
  caracteres, começando por letra) é o código do emissor na B3, o mesmo do 3º ao 6º caractere do
  ISIN brasileiro: é por ela que ticker e ISIN chegam à companhia (`ingest/cvm_fca.py`).
- **CNPJ alfanumérico:** desde julho de 2026 a Receita Federal emite CNPJs novos com letras (IN RFB
  2.229/2024). As 12 primeiras posições (raiz e ordem) têm letras maiúsculas ou números; os 2 dígitos
  verificadores continuam números, e os CNPJs só com números continuam valendo. O dígito verificador é
  o módulo 11 de sempre, com cada caractere valendo o código ASCII menos 48 (os números valem 0 a 9, "A"
  vale 17 e "Z" vale 42), conforme o manual da Receita. Guardado sem máscara e em maiúsculas. Vale para
  o `CNPJ:` dos fundos e o `BR:CNPJ:` das empresas.
- **Item de composição sem identificador de ativo** (ex.: ação no N-PORT, que não traz ticker): o item
  aponta direto para o `empresa_id`, sem `ativo_id`. A classe (ex.: classe A ou C) vem do nome do título,
  só para exibição.

### 3. Formato do `empresa_id`

Derivado só de identificadores públicos e sem licença, na ordem de prioridade:

| Prioridade | `empresa_id` | Fonte (`docs/matriz_de_dados.md`) |
|---|---|---|
| 1 | `BR:CNPJ:` + CNPJ de 14 caracteres (numérico ou alfanumérico, seção 2) | CVM, cadastro de companhias abertas (fonte 3) |
| 2 | `US:CIK:` + 10 dígitos | SEC EDGAR (fonte 7) |
| 3 | `LEI:` + 20 caracteres | campo `lei` do N-PORT (fonte 6; D-08, sem a API do GLEIF) |

- Uma empresa brasileira com ADR na bolsa americana fica com o CNPJ.
- O mesmo código sai em qualquer máquina, sem banco nem contador central.
- A empresa recebe o identificador de maior prioridade que se conhece. Quando aparece um de prioridade maior
  (ex.: uma empresa conhecida só pelo LEI ganha o CIK) ou o identificador público muda (fusão, troca de
  CNPJ), o antigo vira apelido do novo. Um `empresa_id` nunca é reaproveitado para outra empresa.
- Uma empresa vista só pelo LEI (no N-PORT) e a mesma empresa vista pelo ticker (na carteira) só se juntam
  quando a tabela da seção 4 liga o LEI ao CIK.
- Nos testes, só identificadores sintéticos, com prefixo `ZZ:`.

### 4. Tabela de identificadores

- **Por ativo:** `ativo_id`, ticker da B3, ticker americano, ISIN (só da lista permitida), CNPJ (fundos) e
  `empresa_id` (ações).
- **Por empresa:** `empresa_id`, CNPJ, CIK, LEI, tickers e a lista de nomes (o nome jurídico muda com o
  tempo).
- **CUSIP e ISIN fora da lista:** campo opcional, **desligado por padrão**. Só pode ser ligado com licença
  da CGS, por decisão conjunta.
- **Cobertura:** para a empresa "escondida" ser detectada, a tabela precisa cobrir as empresas de todos os
  ETFs americanos que o produto abre, e não só as do escopo do IrRAE: cerca de 500 no IVV e 3.500 no VTI.
- **Fonte da ligação:** `company_tickers.json` (ticker → CIK) e GLEIF (LEI), liberados pelo M1 em 11/10/2026
  (fontes 7 e 16 de `docs/matriz_de_dados.md`; antes estavam em espera, na seção 4 de
  `docs/decisoes_m1_irrae_v1.1.md`). O CIK é a chave e o ticker é só um atributo, porque a SEC não garante
  que o arquivo de tickers esteja correto ou completo. A curadoria à mão continua para o que essas fontes não
  ligarem *(a conferir no PR: se os dados de submissions da SEC, fonte 7, trazem tickers e LEI por CIK)*. A
  cobertura da tabela entra como dívida técnica no PR de código.
- **Nomes:** um nome só liga a uma empresa se for igual a um nome da lista dela, depois de uma
  normalização simples definida no código (maiúsculas e espaços). Nunca pelo "mais parecido".
- **Sem ligação:** ação com LEI fora da tabela vira a empresa `LEI:` + LEI, sem classificação, até a
  tabela ligá-la a um CIK. Ação sem LEI e com nome fora da lista vai para "não identificado" e para
  revisão manual.

### 5. Entrada do POST /raiox

Cada posição passa a ter `identificador` e `tipo_identificador`, no lugar do campo `isin`:

| `tipo_identificador` | Validação |
|---|---|
| `isin` | formato, dígito verificador e país na lista permitida |
| `ticker_b3` | 4 letras e 1 ou 2 dígitos (ex.: PETR4, BOVA11, BDRs como AAPL34) *(a conferir no PR)* |
| `ticker_eua` | 1 a 5 letras, com classe opcional (ex.: BRK.B) *(a conferir no PR)* |
| `cnpj` | 12 letras maiúsculas ou números e 2 dígitos verificadores (CNPJ alfanumérico, seção 2); aceita a máscara (ex.: `12.ABC.345/01DE-35`) e letras minúsculas, normalizadas antes de validar |

- **Ação americana entra só pelo ticker.** Sem guardar ISINs americanos, não há como ligar um ISIN americano
  a uma empresa. Um ISIN de país fora da lista recebe 422, com um motivo que pede o ticker.
- Identificador válido mas desconhecido continua entrando como uma empresa sem classificação, como
  hoje: o próprio `ativo_id` faz o papel de `empresa_id` até a tabela ligá-lo a uma empresa.
- Continua valendo a regra das mensagens de erro: nunca repetir o valor enviado.
- Os leitores de CSV (ADR 0002) já sabem a origem do arquivo: a B3 traz ticker da B3 e a Avenue traz ticker
  americano.
- **Ticker da B3 sem ISIN conhecido** (decisão de 13/10/2026): vira o código interno `B3:` +
  ticker (seção 2). A tabela de identificação liga cada ticker ao `ativo_id` (ISIN, `B3:` ou o
  `CNPJ:` do fundo listado). As ligações que as fontes não fazem sozinhas ficam na curadoria
  versionada (`backend/cargas/curadoria/`).

### 6. Ingestão

- **Composições da CVM (CDA):** um ISIN de país fora da lista (ex.: ação americana dentro de um fundo
  brasileiro) é trocado pelo ticker na ingestão, e o ISIN é descartado. Sem ticker, o ativo vai para "não
  identificado". Confirmado pelo M1. O CDA traz ticker e ISIN juntos no bloco de ações e só o ticker
  no arquivo dos ETFs: a tradução pelo bloco de ações e a ligação de reserva pelo CNPJ do emissor
  estão no ADR 0008.
- **N-PORT:**
  - A ação é ligada à empresa pelo LEI (válido pelo ISO 17442) ou, sem LEI, pelo nome (seção 4). Classes
    da mesma empresa somam pelo LEI (D-08). O ticker é lido quando vier preenchido.
  - O campo `identifiers/other` ("Inhouse Asset ID") não é usado: na maior parte das linhas é o próprio
    CUSIP.
  - A linha de reinvestimento da garantia de empréstimo de títulos sai da composição; sem isso a soma
    passa de 100% e o "não identificado" fica negativo *(a conferir no PR: como identificar a linha no
    XML)*.
  - CUSIP e ISIN americano só passam pela memória durante a leitura. Nenhuma tabela deles é gravada no
    repositório nem no banco. O lote do IrRAE segue a R-01.
- **Cobertura do N-PORT:** só fundos registrados nos EUA pela lei de 1940. Os ETFs UCITS são aproximados
  pelo ETF americano do mesmo índice, com rótulo (regra do produto); fundos brasileiros vêm da CVM; ETFs
  que não são fundos de 1940 (ex.: ouro ou cripto à vista) não têm N-PORT e vão para "não aberto". A
  data-base (`repPdDate`) é registrada; o atraso é de cerca de 60 dias.

## Consequências

- **Regras:** muda a regra do `CLAUDE.md`; o ADR 0003 e o item 3 do ADR 0002 apontam para este ADR.
- **Código, em PRs pequenos e com teste primeiro:**
  1. Motor: `isin` vira `ativo_id`, e a agregação agrupa por `empresa_id`, com o tipo e a % de cada classe;
     item de composição pode apontar direto para a empresa. Fecha a DT-3.
  2. Dados de exemplo: uma empresa sintética com duas classes de ações.
  3. API: a entrada nova (seção 5) e o `empresa_id` na resposta. Muda o contrato da API, mas o front ainda
     não o consome.
  4. IrRAE: a entrada da D-17 passa a usar o `ativo_id`.
  5. Ingestão do N-PORT para o produto (seção 6) e a tabela de empresas (seção 4), com a dívida técnica
     da cobertura.
- **Testes:** a maior parte da mudança é renomear `isin` para `ativo_id`. Faz parte desta decisão, não é
  para fazer teste passar.
- **`backend/CLAUDE.md`:** a regra sobre validação de identificadores muda no PR da API, junto com o código.

## Alternativas descartadas

- **Manter o ISIN e esperar a resposta da CGS:** sem custo agora, mas, se a resposta for tardia ou negativa,
  a troca fica mais cara com o banco e as telas prontos.
- **`empresa_id` opaco e sequencial:** exige um registro central (o banco), que ainda não existe, e não sai
  igual em máquinas diferentes.
- **Licenciar o CUSIP:** custo desconhecido. Continua possível depois, pelo campo opcional da seção 4.
- **Ligar nomes pelo "mais parecido":** um erro silencioso juntaria empresas diferentes e mudaria a
  exposição sem aviso.
