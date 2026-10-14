# Curadoria manual da identificação

Conferido em 13/10/2026. Ligações que as fontes não fazem sozinhas (ADR 0005, seção 4; ADR 0008,
etapa 4). A carga de cadastro (`python -m cargas.cadastro`) lê estes arquivos toda vez, e uma linha
daqui vale mais que a fonte automática. Toda linha nova passa pela revisão do PR.

Formato: CSV em UTF-8, separador `;`, com cabeçalho. A carga confere o formato da raiz e do ticker e
o dígito verificador do CNPJ; uma linha errada faz a carga parar.

## `emissores_b3.csv`

A raiz do ticker (os 4 primeiros caracteres, o código do emissor na B3) ligada à companhia, para as
companhias cujo código de negociação vem errado ou vazio no FCA. Sem esta linha, as ações delas
dentro dos fundos ficam sem empresa e sem setor.

- `raiz`: 4 caracteres, começando por letra (ex.: `BPAC`);
- `cnpj`: o CNPJ da companhia, sem máscara, como está na tabela `geral` do próprio FCA;
- `nome`: o nome da companhia no FCA;
- `motivo`: por que a fonte automática não liga.

Em 13/10/2026, as 5 linhas cobriam 9,6% do valor das ações brasileiras dentro dos fundos (CDA de
agosto de 2026).

## `fundos_listados.csv`

O ticker de um ETF ou FII ligado ao CNPJ do fundo, para os fundos que a carga não liga sozinha (ela
só acha os que aparecem emprestados no CDA). Começa vazio: entra o que os testadores tiverem.

- `ticker`: o código na B3 (ex.: `ZZZZ11`);
- `cnpj`: o CNPJ da classe do fundo, sem máscara;
- `nome`: o nome do fundo;
- `fonte`: onde a ligação foi conferida (ex.: o regulamento do fundo no site da CVM).
