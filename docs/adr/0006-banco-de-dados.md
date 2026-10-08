# ADR 0006: Banco de dados (PostgreSQL)

- **Status:** aceito em 2026-10-08
- **Data:** 2026-10-07
- **Decisor:** Lucas (Membro 2), por ser decisão de engenharia (ADR 0004). O M1 revisa a lista de
  espera (dado pessoal) e as tabelas do IrRAE.
- **Relacionados:** ADR 0003 (Decimal com 50 dígitos), ADR 0004 (IrRAE em lote, resultado gravado no
  banco), ADR 0005 (`ativo_id` e `empresa_id`), DT-1 (PTAX em memória).
- **Fora do escopo:** hospedagem, backups gerenciados e retenção de logs (ADR próprio); carteiras de
  usuários: no protótipo 1 não são gravadas (ver "Fase atual" no CLAUDE.md); a fase com contas terá
  ADR próprio.

## Contexto

Hoje a API lê um conjunto de exemplo sintético em JSON e guarda a PTAX em memória (DT-1). O protótipo 1
precisa guardar dados públicos (composições de fundos da CVM e da SEC, identificação de ativos e
empresas, classificação, PTAX e resultados do IrRAE) e o único dado pessoal do projeto: o e-mail da
lista de espera.

## Decisões

### 1. Tecnologia

- PostgreSQL, na versão que o provedor oferecer: a confirmar no ADR de hospedagem (hoje existem o 17 e
  o 18). No desenvolvimento, a imagem oficial dessa versão no Docker, fixada por digest, acessível só
  por 127.0.0.1 e sem senha (nenhum segredo no repositório).
- SQLAlchemy 2 Core (sem ORM), driver psycopg 3 e migrações com Alembic.
- Conexão pela variável de ambiente `RX_BANCO_URL`, nunca em arquivo do repositório.
- Datas em `DATE`; momentos em `TIMESTAMPTZ`, sempre em UTC; identificadores em `TEXT`.

### 2. Esquemas e tabelas

Dois esquemas, para as permissões e as regras de dado pessoal valerem por esquema. O esquema
`public`, que o PostgreSQL cria sozinho, fica sem uso e sem permissão para ninguém.

| Esquema | Conteúdo |
|---|---|
| `ref` | Dados públicos de referência: identificação, cargas, composições, classificação, PTAX, tabelas do IrRAE e as visões dos dados vigentes |
| `app` | Dados da aplicação: `lista_espera`, `lista_espera_acesso` e as funções de acesso à lista. É o único esquema com dado pessoal |

As tabelas abaixo são indicativas: dizem o que cada uma guarda. O esquema exato (colunas, tipos e
índices) fica nas migrações.

**Identificação (ADR 0005).** A curadoria manual continua no arquivo versionado do ADR 0005; o banco
recebe uma cópia publicada por carga.

| Tabela | Conteúdo |
|---|---|
| `empresa` | `empresa_id` (chave), nome, CNPJ, CIK, LEI |
| `empresa_apelido` | identificador antigo ou de menor prioridade → `empresa_id` |
| `ativo` | `ativo_id` (chave), tipo, `empresa_id` (só ações), ticker da B3, ticker americano, ISIN (só países da lista permitida), nome |
| `fundo` | `fundo_id` (chave; também é um `ativo`), CNPJ, nome, origem (CVM ou N-PORT), `aproximado_por` (UCITS) |

**Dados carregados.**

| Tabela | Conteúdo |
|---|---|
| `carga` | `carga_id`, tipo (composições CVM, composições N-PORT, identificação, classificação, PTAX), fonte, data de referência, status, início, publicação, linhas, motivo do erro |
| `composicao` | `composicao_id`, `carga_id`, `fundo_id`, data de referência, patrimônio líquido |
| `composicao_item` | `composicao_id`, ordem, `ativo_id` (pode ser nulo), `empresa_id` (item sem ativo, como no N-PORT), tipo, valor como a fonte informa, peso, ativo-objeto (derivativo), emissor (crédito) |
| `classificacao` | `carga_id` (a versão), `empresa_id`, setor, origem e status do setor |
| `classificacao_tema` | `carga_id`, `empresa_id`, tema, subtema, peso, origem, status, P5 e P95 (faixa do IrRAE), `execucao_id` de origem (quando a linha vem do IrRAE) |
| `ptax` | data da cotação (chave), valor, `carga_id` |
| `lista_espera` | e-mail normalizado (chave), data de entrada, versão do aviso de privacidade |
| `lista_espera_acesso` | data, quem, motivo, operação (leitura ou exclusão) e quantidade de e-mails. Nunca o e-mail |

**IrRAE (ADR 0004).**

| Tabela | Conteúdo |
|---|---|
| `irrae_execucao` | `execucao_id`, versão do modelo, versão da configuração, semente, data dos dados, status, início, publicação |
| `irrae_resultado` | `execucao_id`, `empresa_id`, nível (folha ou tema), área, média, P5, P95, selo, componentes ausentes |
| `irrae_area_ativa` | `execucao_id`, `empresa_id`, área. O estado anterior que a histerese usa é o da última execução publicada |

**Do IrRAE para a classificação.**

- `irrae_resultado` é a fonte da verdade do que o modelo calculou: imutável e ligado à execução.
- `classificacao_tema` é a fonte da verdade do que o produto usa: o que foi revisado e publicado.
- O dado passa de um para o outro na revisão do M1 de uma execução publicada. A versão nova da
  classificação é montada a partir da vigente, mais as linhas do IrRAE que o M1 aprovou: a média vira
  o peso, P5 e P95 são copiados, e a linha guarda o `execucao_id` de origem e o status aprovado.
- Na classificação, os números nunca são recalculados nem editados. Mudar um número exige uma nova
  execução do IrRAE ou uma linha manual (origem manual, sem faixa).
- Cada versão da classificação é uma foto completa: carrega as linhas da versão anterior que
  continuam valendo. Uma versão só com o resultado novo do IrRAE apagaria da tela o que já estava
  aprovado.
- A faixa de um tema não é a soma das faixas dos subtemas. Quando a X-02 for decidida, a
  classificação ganha a faixa do tema, copiada do nível tema de `irrae_resultado`.

### 3. Versionamento e publicação

- Linha de dado nunca é alterada: só inserida. Uma correção é uma nova carga, que substitui a anterior.
  Apagar, só na retenção de composições (seção 5).
- Toda carga nasce `carregando`, registrada numa transação própria (fica visível mesmo se o processo
  cair), e termina `publicada` ou `com_erro`. Carga publicada não volta atrás. Carga parada em
  `carregando` além do tempo limite vira `com_erro` no início da carga seguinte.
- Composição vigente de um fundo: a de data de referência mais recente entre as cargas publicadas; se
  houver duas do mesmo mês, vale a publicada por último.
- Classificação: cada versão é uma carga do tipo classificação com a foto completa, e a vigente é a
  última publicada. "Publicada" vale para a versão; "aprovado" é a revisão de cada linha (CLAUDE.md).
  A visão `classificacao_vigente` mostra só linhas aprovadas: nada entra no produto com status
  rascunho.
- **Pendente (decisão conjunta com o M1):** mostrar também linhas em rascunho, como "preliminares",
  com selo e texto de tela aprovados pelo M1. O motor e a API já separam o selo confirmado do
  preliminar, mas, com a regra acima, só chegam linhas aprovadas e o selo preliminar fica sem uso
  até essa decisão.
- O IrRAE segue o mesmo ciclo em `irrae_execucao`.
- A API lê só por visões dos dados vigentes (ex.: `composicao_vigente`, `classificacao_vigente`). As
  tabelas-base e as cargas não publicadas não ficam visíveis para ela.

### 4. Números

- Todo valor e peso em `NUMERIC` sem precisão declarada, que guarda o número exato e comporta o
  `Decimal` de 50 dígitos do ADR 0003. Nenhuma coluna `real`, `double precision` ou `float`.
- Guardamos o valor como a fonte informa (R$ e patrimônio na CVM; `pctVal` no N-PORT) e o peso
  calculado na carga com `Decimal` de 50 dígitos. O valor original permite auditar e recalcular.
- O IrRAE calcula em `float` e converte para `Decimal`, truncado, antes de gravar (ADR 0004).
- O psycopg devolve `NUMERIC` como `Decimal`; o código nunca converte para `float`.

### 5. Carga em lote e retenção

1. Registra a carga como `carregando`.
2. `COPY` dos dados para uma tabela de preparação temporária, da própria sessão: some sozinha ao
   fim da carga, ninguém mais a vê, e a ingestão não precisa de permissão para criar tabelas em
   `ref`.
3. Valida: identificadores (ADR 0005; nenhum CUSIP, SEDOL ou ISIN de país fora da lista permitida),
   datas, soma dos pesos de cada fundo dentro da tolerância, fundos e ativos conhecidos, linhas
   duplicadas.
4. Numa transação só: insere nas tabelas definitivas e marca a carga como `publicada`. Se a validação
   falhar, marca `com_erro` com o motivo e descarta a preparação.

Retenção: cerca de 13 meses de composições, apagadas por composição (cabeçalho e itens), não por
carga. Uma carga mensal da CVM mistura milhares de fundos, e a composição vigente de um fundo que
parou de informar continua dentro de uma carga antiga. A limpeza apaga as composições com data de
referência anterior ao prazo que já foram substituídas por outra publicada do mesmo fundo; nunca a
vigente. O registro da carga fica, como histórico. Antes de fixar o prazo, medir o volume de uma
carga mensal completa da CVM. A primeira composição só passa do prazo daqui a cerca de 13 meses,
então o código da limpeza fica para depois do P3 (seção 9).

### 6. Usuários e permissões

| Usuário | Pode |
|---|---|
| `rx_dono` | É o dono dos esquemas `ref` e `app` e das funções de acesso; usado só pelas migrações |
| `rx_api` | Ler as visões dos dados vigentes (esquema `ref`) e inserir na `app.lista_espera`. Mais nada: nem ler a lista de espera |
| `rx_ingestao` | Gravar cargas, identificação, composições, classificação e PTAX, e ler o que precisa para validar |
| `rx_irrae` | Ler composições e identificação publicadas e gravar só as tabelas do IrRAE |
| `rx_admin_lista` | Papel de grupo, sem login: ler e apagar a `lista_espera`, só pelas funções de acesso registrado. Cada pessoa autorizada (hoje, o M1) entra com o próprio usuário, membro deste grupo, criado no ambiente e não no repositório |

- A API grava na lista de espera com `INSERT ... ON CONFLICT DO NOTHING`, sem `RETURNING`, e sem
  conseguir ler: o `RETURNING` exigiria permissão de leitura e revelaria se o e-mail já estava lá.
  Um e-mail repetido recebe a mesma resposta de sucesso.
- Leitura e exclusão de e-mails (por exemplo, para enviar avisos ou a pedido do titular, pela LGPD)
  só com o `rx_admin_lista`, usado manualmente pelo M1. O `rx_dono` não é usado para isso.
- Cada acesso fica registrado em `lista_espera_acesso`: data, quem, motivo e operação. Como o
  PostgreSQL não dispara gatilho em leitura, o `rx_admin_lista` não acessa a tabela direto: lê e
  apaga por funções que gravam o registro e depois executam a operação (ex.:
  `exportar_lista_espera(motivo)` e `excluir_da_lista_espera(email, motivo)`).
- "Quem" não é parâmetro: a função grava o `session_user`, o usuário pessoal com que a pessoa
  entrou (dentro de uma função SECURITY DEFINER, o `session_user` não muda). Só o motivo vem como
  parâmetro. O registro não guarda o e-mail apagado, senão a exclusão não se cumpriria.
- As funções de acesso são `SECURITY DEFINER`, pertencem ao `rx_dono` e declaram
  `SET search_path` fixo (`pg_catalog, app`), para ninguém desviar a função com um objeto de mesmo
  nome em outro esquema. O `EXECUTE` é retirado de `PUBLIC` (que o PostgreSQL dá por padrão) e dado
  só ao `rx_admin_lista`.
- A API não roda migrações ao subir. As senhas ficam fora do repositório.

### 7. Testes

- `app/core/` continua puro e sem banco (ADR 0003).
- Os testes com banco ficam em `tests/banco/`, separados da suíte que roda sem Docker. No CI, rodam
  num job próprio com a mesma imagem fixada do PostgreSQL.
- Cada rodada aplica as migrações a partir do banco vazio, o que testa as migrações também.
- Os mesmos testes de contrato do `RepositorioDados` rodam contra o `RepositorioExemplo` e o
  `RepositorioPostgres`.
- Testes das permissões:
  - `rx_api` não lê a lista de espera, não vê carga não publicada e não grava composição;
  - o `INSERT ... ON CONFLICT DO NOTHING` do `rx_api` na `lista_espera` funciona sem permissão de
    leitura e dá a mesma resposta para e-mail novo e repetido;
  - `rx_admin_lista` só lê e apaga pelas funções, cada chamada deixa um registro com o
    `session_user` do usuário pessoal e sem o e-mail, e ele não acessa nenhuma outra tabela;
  - as funções de acesso são `SECURITY DEFINER` com `search_path` fixo, e nem `PUBLIC` nem
    `rx_api` conseguem executá-las.
- Os testes do motor e da API continuam com dados sintéticos que têm linhas preliminares (o
  `RepositorioExemplo`), para o selo preliminar seguir testado até a decisão com o M1. Os testes de
  contrato cobrem o que os dois repositórios têm em comum; o filtro de linhas aprovadas da
  `classificacao_vigente` é testado só no `RepositorioPostgres`.

### 8. Migrações

- Alembic, só para frente: nenhuma migração tem volta, e um erro se corrige com uma migração nova.
- Toda migração é revisada no PR; o que o Alembic gera sozinho é só ponto de partida.
- Em produção: backup antes de migrar (como, no ADR de hospedagem), e a migração roda como passo
  separado, com `rx_dono`.

### 9. Fases de implementação

Este ADR descreve o desenho-alvo. A implementação segue o prazo do protótipo:

| Fase | O que entra |
|---|---|
| **Antes do P3** | Esquema `ref` com identificação, cargas, composições, classificação simples (setor oficial e linhas manuais) e PTAX, e as visões vigentes. Os usuários `rx_dono`, `rx_api` e `rx_ingestao`. O `RepositorioPostgres`, a carga da CVM e a PTAX (fecha a DT-1). A `app.lista_espera`, o `rx_admin_lista` e as funções de acesso entram aqui só se a landing já estiver recolhendo e-mails; senão, vão para a fase seguinte. |
| **Depois do P3** | As tabelas do IrRAE e o `rx_irrae`, o fluxo do IrRAE para a classificação, a faixa do tema (X-02), o código da retenção e, se ainda não tiverem entrado, a lista de espera, o `rx_admin_lista` e as funções de acesso. |
| **Fase com contas** | A seção "Evolução prevista", com ADR próprio. |

A lista de espera, o `rx_admin_lista` e as funções de acesso entram sempre juntos: a API não pode
começar a gravar e-mails antes de existir o único caminho autorizado para lê-los e apagá-los.

**Alternativa se o banco atrasar:** o teste fechado do P3 pode usar um repositório que lê os
arquivos das cargas publicadas (as mesmas validações da seção 5, gravadas em arquivo), implementando
o `RepositorioDados`. O `RepositorioPostgres` entra logo depois, sem mudar a API nem o motor.

## Consequências

- A DT-1 fecha no PR que levar a PTAX para o banco (ingestão diária e a API lendo a tabela).
- `RepositorioPostgres` passa a implementar o `RepositorioDados`; o `RepositorioExemplo` continua
  para testes e desenvolvimento.
- O GET /fontes usa as cargas publicadas para mostrar a data de cada fonte.
- Novo job de CI, `banco`.
- Pendente com o M1: mostrar ou não linhas preliminares na tela (seção 3).
- Para o M1 tratar na política de privacidade:
  - se os avisos forem enviados por um serviço de e-mail marketing, esse serviço passa a tratar os
    e-mails como operador (LGPD);
  - um e-mail excluído a pedido do titular continua nos backups até eles expirarem.
- Implementação em PRs pequenos, na ordem das fases da seção 9: primeiro o Postgres local, o
  esquema inicial, os usuários e o teste das migrações; depois o `RepositorioPostgres` com os
  testes de contrato, a carga da CVM e a PTAX.

## Evolução prevista (fase com contas)

Previsão, não decisão: a fase com contas terá ADR próprio ("Fase atual" no CLAUDE.md). O que este
desenho já prepara:

- **Onde ficam os dados de usuário:** contas, carteiras salvas e regras de alerta são dado pessoal
  e não entram em `ref`. A recomendação é o esquema `app`, junto da lista de espera, com Row-Level
  Security; a alternativa é um esquema próprio para as carteiras. Decide-se no ADR da fase.
- **Contas:** e-mail, hash da senha com Argon2id (ADR 0001), data de criação e versão dos termos e
  do aviso de privacidade aceitos.
- **Carteiras salvas:** posições por `ativo_id`, valor e moeda, criptografadas pela aplicação (com
  a chave fora do banco), e não só pelo disco do provedor. A análise continua no motor, em memória.
- **Isolamento entre usuários:** Row-Level Security do PostgreSQL, para cada consulta da API ver só
  as linhas do usuário logado, mesmo se o código errar o filtro.
- **Dado de usuário pode mudar e ser apagado:** a regra "só acrescenta" (seção 3) vale para os
  dados públicos de `ref`. O usuário edita a carteira, e a exclusão da conta apaga contas, carteiras
  e alertas de vez (LGPD), sujeita ao prazo dos backups.
- **Alertas de concentração:** as regras por conta e o histórico dos avisos enviados.
- **Permissões:** a API ganha acesso às tabelas de conta e carteira, com a Row-Level Security; o
  `rx_admin_lista` continua só com a lista de espera.

## Alternativas descartadas

- **SQLite nos testes:** o comportamento difere do PostgreSQL (tipos, permissões, `COPY`).
- **ORM do SQLAlchemy:** mais camadas do que o necessário para dados públicos e cargas em lote; com
  o Core, o SQL fica explícito.
- **Atualizar composições no lugar:** perde o histórico e a auditoria, e uma carga que falha no meio
  deixa dados misturados.
- **`float` no banco:** perde exatidão (ADR 0003).
- **Um usuário só para tudo:** uma falha na API exporia a lista de espera e permitiria gravar dados.
