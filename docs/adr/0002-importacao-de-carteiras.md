# ADR 0002: Importação de carteiras de corretoras e bancos

- **Status:** proposto (aguardando decisão do Lucas sobre ampliar o escopo)
- **Data:** 2026-09-25
- **Decisor:** Lucas (Membro 2)

## Contexto

O escopo do protótipo 1 prevê importação de CSV só da B3 e da Avenue, mais o cadastro manual. Surgiu a pergunta: dá para reconhecer o arquivo de qualquer corretora, e também de bancos?

Não existe padrão: cada instituição exporta num formato próprio (colunas, separador, formato de número e de data, CSV ou Excel), e esses formatos mudam sem aviso. Um único leitor universal não é viável. É viável cobrir a maior parte dos casos com três camadas.

## Proposta: três camadas de leitores

### 1. B3: um leitor que cobre todas as corretoras brasileiras

A Área do Investidor da B3 consolida as posições de todas as corretoras e bancos brasileiros em que a pessoa tem conta (XP, Rico, Clear, BTG, Nubank, Inter, Itaú, Bradesco etc.), porque os ativos negociados em bolsa ficam registrados na B3.

- **Entra:** ações, FIIs, ETFs, BDRs, Tesouro Direto e renda fixa registrada na B3.
- **Não entra (a confirmar):** fundos de investimento comuns, não negociados em bolsa. Eles ficam com o administrador do fundo, não na B3.
- **Formato (a confirmar):** a B3 costuma exportar em Excel (.xlsx), não em CSV. Se for isso, o leitor aceita os dois.

Por isso o escopo original escolheu B3 e Avenue: a B3 cobre o Brasil inteiro, e a Avenue cobre uma conta no exterior.

### 2. Leitores específicos para contas no exterior

Corretoras internacionais (Avenue, Nomad, Inter US, XP Internacional, Interactive Brokers etc.) não passam pela B3. Cada uma precisa de um leitor próprio, pequeno, que só traduz as colunas daquele formato para o modelo de posição do projeto (`Posicao`: ISIN, valor em reais e tipo).

- O código fica preparado para acrescentar um leitor novo sem mexer nos outros.
- Cada leitor precisa de um arquivo de exemplo **com dados inventados** daquele formato, que vira fixture de teste.
- Um leitor quebra se a instituição mudar o arquivo; o teste com a fixture mostra quando isso acontecer.

### 3. Leitor genérico, com mapeamento das colunas

Para qualquer outra planilha, incluindo exportações de bancos:

1. **Detecção automática:** o código procura nos cabeçalhos nomes conhecidos ("ticker", "código", "ativo", "ISIN", "quantidade", "valor", "saldo", "moeda" etc.).
2. **Se não reconhecer:** a tela mostra as colunas do arquivo e a pessoa escolhe qual é o ativo, qual é a quantidade ou o valor e qual é a moeda.
3. **Identificação do ativo:** ticker vira `ativo_id` (ADR 0005) pela fonte aprovada em `docs/matriz_de_dados.md`. Fundos de banco são identificados pelo CNPJ ou pelo nome, usando o cadastro de fundos da CVM.

Em todas as camadas vale a regra do projeto: o arquivo é processado só em memória, nada da carteira é gravado ou registrado em log, e as mensagens de erro não repetem valores do arquivo.

## Limites

- **Extratos em PDF**, comuns em bancos, ficam de fora: ler PDF de extrato é frágil e cada banco tem um layout.
- **Open Finance** seria a solução universal (dados padronizados, direto das instituições), mas está fora do escopo do protótipo 1 por decisão do projeto.

## Recomendação para o protótipo 1

| Leitor | Cobre |
|---|---|
| B3 (CSV e Excel) | Todas as corretoras e bancos brasileiros, para os ativos registrados na B3 |
| Avenue | Conta nos EUA pela Avenue |
| Genérico, com mapeamento manual das colunas | Qualquer outra planilha, incluindo exportações de bancos |

Depois, conforme a validação com usuários (M1), entram leitores específicos para as corretoras internacionais mais usadas.

## Consequências, se aceito

- O leitor genérico **amplia o escopo** do protótipo 1. É preciso atualizar o CLAUDE.md da raiz.
- A etapa de escolher colunas precisa de textos novos em `docs/textos_telas.md`.
- Ler Excel exige uma dependência nova no backend (por exemplo, `openpyxl`).

## Pendências para começar qualquer leitor

- Um arquivo exportado da B3 e um da Avenue **com os valores trocados por números inventados**, ou a descrição das colunas de cada um (nomes, separador, formato de número e de data, encoding).
- Confirmar os dois pontos marcados "a confirmar" acima.
