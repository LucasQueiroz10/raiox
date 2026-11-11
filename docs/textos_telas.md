# Textos das telas

Fonte única de todos os textos da interface da Sagital.

## Regras

- O front copia cada texto **literalmente** para `frontend/src/textos.ts`, sem mudar nenhuma palavra, acento ou pontuação.
- Só textos com status **aprovado** entram no código. Textos em **rascunho** ou **a escrever** não aparecem na interface.
- Os textos descrevem a exposição da carteira e **nunca recomendam** compra, venda ou rebalanceamento.
- Toda mudança em um texto aprovado volta para **rascunho** e passa por nova revisão (Membro 1).
- Cada texto tem um identificador (`tela.nome`) que o código usa para encontrá-lo.
- Trechos entre chaves, como `{data}`, são preenchidos pelo sistema com o valor da análise.

Status possíveis: `a escrever` · `rascunho` · `aprovado`

Com o produto arquivado (ADR 0009), a interface publicada é só a da vitrine, que tem textos próprios
(seção "Vitrine"). As demais seções ficam para a retomada do produto.

---

## Vitrine

Partem de `docs/vitrine/especificacao.md` e foram reescritos em 10/11/2026, a pedido do Lucas, para
revisão do M1.

Critérios da reescrita:
- o visitante não traz carteira: falamos com "você" e da carteira como "esta carteira";
- termo técnico (IrRAE, P5, P95, look-through) só um clique abaixo, nunca no primeiro nível;
- nenhum verbo de recomendação; o termo é sempre "faixa estimada";
- sem travessão longo; o travessão curto aparece só dentro das faixas numéricas (`69% [56–81]`);
- cada ideia dita uma vez; o título já explica, o texto embaixo só acrescenta.

Glossário, para manter os mesmos termos em todo o site:
- **cadeia de IA:** o tema medido (nome na configuração do IrRAE: Cadeia de IA);
- **exposição:** quanto da carteira, ou da empresa, depende da cadeia de IA;
- **faixa estimada:** a faixa entre o P5 e o P95 dos sorteios do modelo;
- **coberta / não coberta:** parte da carteira com ou sem estimativa;
- **abrir (um ETF):** trocar o ETF pelas empresas que ele tem.

### Navegação e moldura

| Identificador | Texto | Status |
|---|---|---|
| `vitrine.nav.inicio` | Início | rascunho |
| `vitrine.nav.carteiras` | Carteiras | rascunho |
| `vitrine.nav.metodologia` | Como medimos | rascunho |
| `vitrine.nav.fontes` | Fontes | rascunho |
| `vitrine.nav.pular_para_conteudo` | Pular para o conteúdo | rascunho |
| `vitrine.dados_ilustrativos` | Números ilustrativos. Ainda não foram calculados com dados reais. | rascunho |
| `vitrine.rodape` | Projeto independente, sem fins comerciais. Não é recomendação de investimento. Sem vínculo com a SEC, a CVM, a B3, a S&P Dow Jones Indices, os gestores dos ETFs ou as empresas citadas. Nomes de índices, fundos e empresas pertencem aos seus titulares e aparecem só para identificar as carteiras. | rascunho |
| `vitrine.rodape.autoria` | | a escrever |

### Início

| Identificador | Texto | Status |
|---|---|---|
| `vitrine.inicio.titulo` | Quanto uma carteira depende, de fato, da cadeia de IA? | rascunho |
| `vitrine.inicio.subtitulo` | Abrimos três carteiras públicas até as empresas e medimos quanto cada empresa depende da cadeia de IA. | rascunho |
| `vitrine.inicio.aviso` | Projeto independente, sem fins comerciais. Não é recomendação de investimento. | rascunho |
| `vitrine.inicio.escolha` | Escolha uma carteira | rascunho |
| `vitrine.inicio.camadas.titulo` | Do ETF à empresa, em quatro camadas | rascunho |
| `vitrine.inicio.camadas.carteira` | Carteira: partimos dos pesos de cada posição. | rascunho |
| `vitrine.inicio.camadas.fundos` | Fundos: trocamos cada ETF pelas empresas que ele declara ter. | rascunho |
| `vitrine.inicio.camadas.empresas` | Empresas: somamos a mesma empresa quando ela aparece por mais de um caminho. | rascunho |
| `vitrine.inicio.camadas.exposicao` | Exposição: medimos quanto cada empresa depende da cadeia de IA. | rascunho |

### Carteiras

| Identificador | Texto | Status |
|---|---|---|
| `vitrine.carteira.big_techs.nome` | 4 big techs americanas | rascunho |
| `vitrine.carteira.big_techs.descricao` | NVIDIA, Amazon, Apple e Microsoft, 25% cada. | rascunho |
| `vitrine.carteira.sp500.nome` | S&P 500 | rascunho |
| `vitrine.carteira.sp500.descricao` | Um ETF que replica o índice (IVV), aberto pela carteira que ele declara à SEC. | rascunho |
| `vitrine.carteira.ibovespa.nome` | Ibovespa | rascunho |
| `vitrine.carteira.ibovespa.descricao` | Um ETF que replica o índice (BOVA11), aberto pela carteira que ele informa à CVM. | rascunho |
| `vitrine.carteira.etf_do_indice` | Carteira do {etf}, ETF que replica o índice, em {data}. Não é a composição oficial do índice. | rascunho |
| `vitrine.carteira.data_referencia` | Carteira de {data} | rascunho |
| `vitrine.carteira.data_calculo` | Calculado em {data} | rascunho |

### Raio-x da carteira

| Identificador | Texto | Status |
|---|---|---|
| `vitrine.raiox.exposicao` | Exposição à cadeia de IA | rascunho |
| `vitrine.raiox.fora_do_tema` | Fora da cadeia de IA | rascunho |
| `vitrine.raiox.nao_coberto` | Não coberta | rascunho |
| `vitrine.raiox.por_setor` | Por setor | rascunho |
| `vitrine.raiox.por_tema` | Por tema | rascunho |
| `vitrine.raiox.setor_e_tema` | Por setor, cada empresa entra inteira em um setor. Por tema, ela é repartida pelo que de fato faz. Por isso as duas visões dão números diferentes. | rascunho |
| `vitrine.raiox.subtemas` | Onde está a exposição | rascunho |
| `vitrine.raiox.cobertura` | Estimativa completa para {percentual} da carteira | rascunho |
| `vitrine.raiox.cobertura.so_setor` | Estimada só pelo setor: {percentual} | rascunho |
| `vitrine.raiox.cobertura.nota` | A parte não coberta fica de fora da estimativa. Não completamos com número inventado. | rascunho |
| `vitrine.raiox.empresas` | Empresas | rascunho |
| `vitrine.raiox.empresas.peso` | Peso | rascunho |
| `vitrine.raiox.empresas.contribuicao` | Contribuição | rascunho |
| `vitrine.raiox.empresas.contribuicao_ajuda` | Peso da empresa vezes a exposição dela: quanto ela soma à exposição da carteira. | rascunho |
| `vitrine.raiox.empresas.ver_todas` | Ver as {quantidade} empresas | rascunho |
| `vitrine.raiox.aberto_em` | 100% no {etf}, aberto em {quantidade} empresas. | rascunho |

### Faixa e selo

| Identificador | Texto | Status |
|---|---|---|
| `vitrine.faixa.rotulo` | faixa estimada | rascunho |
| `vitrine.faixa.ajuda_empresa` | Nos {sorteios} sorteios do modelo, 5% dos resultados ficaram abaixo desta faixa e 5% acima. | rascunho |
| `vitrine.faixa.ajuda_carteira` | Faixa estimada, supondo que os erros das empresas andam juntos. | rascunho |
| `vitrine.selo.alta` | Faixa estreita | rascunho |
| `vitrine.selo.media` | Faixa média | rascunho |
| `vitrine.selo.preliminar` | Preliminar | rascunho |
| `vitrine.selo.ajuda` | O selo vem da largura da faixa: quanto mais evidência, mais estreita ela fica. | rascunho |

### Empresa

| Identificador | Texto | Status |
|---|---|---|
| `vitrine.empresa.componentes` | De onde vem a estimativa | rascunho |
| `vitrine.empresa.componentes_ajuda` | Quando uma fonte falta, o peso dela passa para as que estão presentes. | rascunho |
| `vitrine.empresa.componente_ausente` | Sem dado | rascunho |
| `vitrine.empresa.fontes` | Documentos usados | rascunho |
| `vitrine.empresa.so_setor` | Ainda não reunimos os documentos desta empresa. A estimativa usa só o setor dela e por isso é preliminar. | rascunho |
| `vitrine.empresa.nao_coberta` | Ainda não estimamos esta empresa. Ela entra na parte não coberta da carteira. | rascunho |

### Metodologia, fontes e erros

| Identificador | Texto | Status |
|---|---|---|
| `vitrine.metodologia.titulo` | Como medimos | rascunho |
| `vitrine.metodologia.dirichlet` | Mais evidência, faixa mais estreita. | rascunho |
| `vitrine.metodologia.nao_faz` | O modelo não prevê preço e não diz o que comprar ou vender. Ele descreve quanto da atividade de cada empresa está ligada à cadeia de IA. | rascunho |
| `vitrine.fontes.titulo` | Fontes e licenças | rascunho |
| `vitrine.erro.carregar` | Não foi possível carregar esta carteira. Recarregue a página para tentar de novo. | rascunho |
| `vitrine.erro.formato` | Os dados desta carteira estão num formato que o site não reconhece. Tente outra carteira. | rascunho |
| `vitrine.erro.pagina` | Esta página não existe. | rascunho |
| `vitrine.erro.voltar` | Voltar às carteiras | rascunho |

Notas para a revisão:

- **"Projeto independente"** (`vitrine.inicio.aviso`, `vitrine.rodape`): a especificação dizia
  "projeto pessoal", mas a vitrine é do Lucas e do M1 (ADR 0009). "Independente" diz que não há
  empresa por trás sem sugerir um autor só.
- **`vitrine.inicio.titulo`:** a frase da especificação ("quanto do seu dinheiro depende...") falava
  do dinheiro do visitante, que não traz carteira. A pergunta agora é sobre "uma carteira", e o
  "de fato" separa depender da cadeia de IA de só parecer uma empresa de IA.
- **`vitrine.faixa.ajuda_empresa`:** explica o P5 e o P95 sem citar "90%", para não ser lido como
  nível de confiança. `{sorteios}` é o `n_amostras` do snapshot.
- **`vitrine.faixa.ajuda_carteira`:** é o rótulo obrigatório da especificação, mantido literal.
  Depende da V-09 do ADR 0009: se o M1 mantiver os dois cenários da D-01, o texto muda. Nunca usar
  "intervalo de confiança", "IC90" ou "conservadora".
- **Selo:** "alta" e "média" viraram "Faixa estreita" e "Faixa média", porque o selo mede a largura
  da faixa, não a exposição. "Alta" sozinho seria lido como exposição alta.
- **`vitrine.raiox.cobertura`:** "IrRAE calculado para X% do peso" virou "estimativa completa",
  para o nome do modelo não aparecer no primeiro nível. O nome IrRAE fica na página "Como medimos".
- **`vitrine.empresa.so_setor` e `vitrine.empresa.nao_coberta`:** explicam o porquê sem mostrar faixa
  inventada (especificação, seção 5.3).
- **`vitrine.metodologia.nao_faz`:** confirmar com o M1 se "quanto da atividade" resume bem os
  componentes A, Ir, B, R, N, C e P.
- **`vitrine.rodape.autoria`:** espera a V-08 (nome e link dos autores).
- Os textos longos da página "Como medimos" entram depois, num bloco próprio.

---

## Landing

| Identificador | Texto | Status |
|---|---|---|
| `landing.titulo` | Veja onde o seu dinheiro está concentrado | rascunho |
| `landing.subtitulo` | Abrimos os fundos e ETFs da sua carteira até as empresas e mostramos quanto você tem em cada empresa, setor e tema, como a cadeia de inteligência artificial. | rascunho |
| `landing.lista_espera.chamada` | Quer saber quando abrirmos para mais pessoas? Deixe seu e-mail. | rascunho |
| `landing.lista_espera.campo_email` | Seu e-mail | rascunho |
| `landing.lista_espera.botao` | Entrar na lista de espera | rascunho |
| `landing.lista_espera.sucesso` | Pronto. Vamos avisar você por e-mail quando houver novidades. | rascunho |
| `landing.lista_espera.erro` | Não foi possível registrar seu e-mail agora. Confira o endereço e tente de novo. | rascunho |
| `landing.aviso_privacidade` | Usamos seu e-mail só para avisos sobre o projeto. Você pode pedir a exclusão a qualquer momento. | rascunho |

## Cadastro

| Identificador | Texto | Status |
|---|---|---|
| `cadastro.titulo` | Sua carteira | rascunho |
| `cadastro.manual.instrucao` | Informe cada ação ou fundo pelo código e o valor que você tem hoje, em reais ou em dólares. | rascunho |
| `cadastro.csv.instrucao` | Ou envie o arquivo de posições exportado da sua corretora. | rascunho |
| `cadastro.csv.b3` | Posição da Área do Investidor da B3 (CSV) | rascunho |
| `cadastro.csv.avenue` | Extrato de posições da Avenue (CSV) | rascunho |
| `cadastro.erro.formato` | Não reconhecemos o formato deste arquivo. Confira se é o arquivo de posições da B3 ou da Avenue, em CSV. | rascunho |
| `cadastro.aviso_nao_gravamos` | Sua carteira é usada só para montar este raio-x. Não gravamos as posições nem os valores, e nada fica salvo no seu navegador. | rascunho |

## Câmbio

| Identificador | Texto | Status |
|---|---|---|
| `cambio.titulo` | Câmbio | rascunho |
| `cambio.ptax_usada` | Valores em dólar convertidos pela PTAX de venda do Banco Central de {data}: R$ {valor} por dólar. | rascunho |
| `cambio.dia_util_anterior` | A PTAX de hoje ainda não foi divulgada; usamos a do último dia útil. | rascunho |
| `cambio.aviso_bcb` | Fonte: Banco Central do Brasil – PTAX (API Olinda), consultado em {data_consulta}. Valores em reais calculados pela Sagital a partir da PTAX de venda. O BCB não se responsabiliza pelo uso destas informações. | rascunho |

`cambio.aviso_bcb`: aviso de responsabilidade do Banco Central que a planilha de fontes (ficha FP-36)
manda repassar ao usuário. Redação proposta pelo M1 em 13/10/2026. `{data_consulta}` é a data em que
a PTAX foi obtida do Banco Central, o campo `ptax.data_consulta` da resposta (a data da própria
cotação está em `cambio.ptax_usada`). Falta
confirmar se a última frase é texto oficial do Banco Central ou redação nossa: a resposta da API PTAX e
a página do conjunto de dados não trazem aviso (conferido em 12/10/2026).

## Raio-X

| Identificador | Texto | Status |
|---|---|---|
| `raiox.titulo` | Raio-X da carteira | rascunho |
| `raiox.por_setor` | Por setor | rascunho |
| `raiox.por_tema` | Por tema | rascunho |
| `raiox.por_subtema` | Por subtema | rascunho |
| `raiox.empresas_escondidas.titulo` | Empresas que você tem por meio de fundos | rascunho |
| `raiox.empresas_escondidas.explicacao` | Estas empresas chegam à sua carteira dentro de fundos e ETFs, às vezes somadas ao que você já tem diretamente. | rascunho |
| `raiox.cobertura` | Cobertura da classificação | rascunho |
| `raiox.nota_cobertura` | A cobertura considera apenas o valor investido em ações. Caixa, títulos públicos, derivativos e valores não identificados não têm setor e ficam fora deste cálculo. | rascunho |
| `raiox.data_composicao` | Composição informada em {data} | rascunho |
| `raiox.rotulo_ucits` | Aproximado pela carteira do ETF americano que segue o mesmo índice. | rascunho |
| `raiox.caixa` | Caixa | rascunho |
| `raiox.credito` | Títulos de crédito privado | rascunho |
| `raiox.titulos_publicos` | Títulos públicos | rascunho |
| `raiox.nao_identificado` | Não identificado | rascunho |
| `raiox.nao_aberto` | Não aberto | rascunho |
| `raiox.nota_derivativos` | NOTA: A dinâmica financeira do contrato de derivativos nao permite quantificar com precisão a exposição ao mercado, logo esse número representa apenas a % investida nesse mecanismo | rascunho |
| `raiox.nota_posicoes_vendidas` | NOTA: As posições vendidas dentro dos fundos reduzem a exposição de formas que não conseguimos medir com precisão; esse número representa apenas o valor vendido. | rascunho |
| `raiox.classes` | Classes de ação: {classes} | rascunho |
| `raiox.demais_empresas` | Mais {quantidade} empresas, que somam {percentual} da carteira | rascunho |
| `raiox.confidencial` | Confidencial | rascunho |
| `raiox.nota_confidencial` | Parte da carteira que o gestor pode manter em sigilo por um período, conforme regra da CVM. | rascunho |
| `raiox.credito_sem_emissor` | Crédito sem emissor identificado | rascunho |
| `raiox.nota_credito_sem_emissor` | Títulos de crédito privado, como debêntures, cuja empresa emissora não conseguimos identificar. | rascunho |
| `raiox.fundos_imobiliarios` | Fundos imobiliários | rascunho |
| `raiox.fii.tijolo` | Tijolo: {segmento} | rascunho |
| `raiox.fii.tijolo_varios_segmentos` | Tijolo, vários segmentos | rascunho |
| `raiox.fii.papel` | Papel | rascunho |
| `raiox.fii.fundo_de_fundos` | Fundo de fundos | rascunho |
| `raiox.fii.generico` | Sem tipo predominante | rascunho |
| `raiox.nota_fii` | Mostramos cada fundo imobiliário pelo que predomina na carteira que ele informa à CVM: imóveis (tijolo), títulos de crédito imobiliário (papel) ou cotas de outros fundos imobiliários (fundo de fundos), quando esse grupo passa da metade do investido. Os imóveis e os títulos de cada fundo não são abertos. | rascunho |

`raiox.fundos_imobiliarios` a `raiox.nota_fii`: textos do PR 4.3 do ADR 0008 (14/10/2026), para o M1
revisar. Cada fatia de `fiis_por_tipo` usa o texto do seu tipo; no tijolo, `{segmento}` é o segmento
como o fundo declara à CVM (ex.: Logística), e sem segmento vale `raiox.fii.tijolo_varios_segmentos`.
A regra do tipo está em `backend/ingest/cvm_fii.py` (matriz de dados, fonte 36).

`raiox.confidencial` e `raiox.nota_confidencial`: decisão do M1 em 12/10/2026 (ADR 0008, seção 7): a
parte em sigilo é uma categoria própria, separada do "não identificado". Texto da nota proposto por ele.

Quando aparecem as notas:

- `raiox.nota_cobertura`: sempre junto do indicador de cobertura.
- `raiox.nota_derivativos`: sempre que o total em derivativos da carteira for diferente de zero.
- `raiox.nota_confidencial`: sempre que a categoria confidencial for diferente de zero.
- `raiox.nota_credito_sem_emissor`: sempre que o crédito sem emissor for diferente de zero, junto do
  valor, separado do crédito com emissor (pedido do M1).
- `raiox.nota_posicoes_vendidas`: sempre que o total em posições vendidas for diferente de zero. O texto deve seguir a linha da nota de derivativos, explicando que a identificação da exposição é limitada.
- `raiox.nota_fii`: sempre que a categoria dos fundos imobiliários for diferente de zero, junto das
  fatias por tipo.

## Avisos comuns

| Identificador | Texto | Status |
|---|---|---|
| `avisos.nao_e_recomendacao` | Este raio-x descreve a sua carteira. Não é recomendação de compra, venda ou de qualquer mudança nos seus investimentos. | rascunho |
| `avisos.creditos_fontes` | Fontes: CVM, Dados Abertos (CDA, FCA, Informe Mensal de FII e Cadastro), licença ODbL; Banco Central do Brasil, PTAX, licença ODbL. Dados processados pela Sagital, que não tem vínculo com essas instituições. | rascunho |
| `avisos.ciclo` | Alguns fundos investem uns nos outros em círculo. Seguimos esse caminho até o valor ficar abaixo de 0,1% e mostramos o restante como não aberto. | rascunho |
| `avisos.fundo_sem_composicao` | Não encontramos a composição de um dos seus fundos. O valor dele aparece como não aberto. | rascunho |

`avisos.creditos_fontes`: fica no rodapé da tela do raio-x, sempre que um raio-x aparece. A licença
ODbL (CVM e Banco Central) exige o crédito onde os dados aparecem; a landing e o cadastro não mostram
esses dados. Junta o texto do M1 de 12/10/2026 ("Fonte: CVM, Dados Abertos (CDA, FCA e Cadastro).
Licença ODbL. Dados processados pelo Projeto RX.") com o crédito que já existia, com o nome da Sagital.
A SEC sai enquanto nenhum dado dela aparece na tela: quando o N-PORT entrar, voltar a citar "SEC,
Estados Unidos". O "Informe Mensal de FII" entrou em 14/10/2026, com os FIIs no raio-x (fonte 36).

## Avisos e erros da API

Um texto para cada código que a API devolve (`avisos[].codigo` e `detail.codigo`).

| Identificador | Texto | Status |
|---|---|---|
| `avisos.ciclo_sem_convergencia` | Um dos seus fundos entra num círculo de investimentos que não fecha. O valor que circula aparece como não aberto. | rascunho |
| `avisos.cadeia_longa` | Um dos seus fundos investe em uma cadeia muito longa de outros fundos. A parte mais distante aparece como não aberta. | rascunho |
| `avisos.limite_de_processamento` | Esta carteira é grande demais para abrir por completo. A parte que não deu para abrir aparece como não aberta. | rascunho |
| `avisos.fundo_sem_identificador` | Um dos seus fundos investe em outros fundos que não conseguimos identificar, como fundos no exterior. Esse valor aparece como não aberto. | rascunho |
| `avisos.composicao_antiga` | Sem composição recente: a última carteira que um dos seus fundos informou à CVM é de {data}, há mais de 90 dias. O raio-x usa essa carteira, que pode ser diferente da atual. | rascunho |
| `avisos.fundo_sem_composicao_utilizavel` | Fundo sem composição utilizável: a carteira que um dos seus fundos informou à CVM não permite calcular quanto vale cada aplicação. O valor dele aparece como não aberto. | rascunho |
| `erros.entrada_invalida` | Alguns dados da carteira não estão no formato esperado. Confira os campos marcados. | rascunho |
| `erros.corpo_grande_demais` | A carteira enviada é grande demais. Divida em partes menores. | rascunho |
| `erros.muitas_analises` | Você fez muitas análises em pouco tempo. Tente de novo em alguns instantes. | rascunho |
| `erros.servidor_ocupado` | Estamos com muitas análises ao mesmo tempo. Tente de novo em alguns instantes. | rascunho |
| `erros.cambio_indisponivel` | Não conseguimos a cotação do dólar agora. Tente de novo mais tarde ou informe os valores em reais. | rascunho |
| `erros.dados_indisponiveis` | Não conseguimos carregar os dados dos fundos agora. Tente de novo em alguns instantes. | rascunho |
| `erros.erro_interno` | Algo deu errado do nosso lado. Tente de novo em alguns instantes. | rascunho |
| `avisos.tipo_corrigido` | Consideramos este ativo como {tipo}, conforme a nossa base de ativos, e não como {tipo_marcado}. | rascunho |
| `avisos.tipo_corrigido.acao` | ação | rascunho |
| `avisos.tipo_corrigido.fundo` | fundo | rascunho |

`avisos.composicao_antiga` e `avisos.fundo_sem_composicao_utilizavel`: pedidos do M1 em 12/10/2026
(ADR 0008, seção 7). Os códigos na API saem do PR 2.1 da carga da CVM; conferir os nomes quando ele
entrar. No primeiro, `{data}` é a data da composição do fundo (`fundos[].data_referencia`); o fundo
continua aberto, com o aviso. O segundo vale para fundo com patrimônio zerado ou negativo, que a carga
registra sem composição.

`avisos.tipo_corrigido`: recomendação de 15/10/2026, aprovada pelo Lucas (não fazia parte da
decisão do tipo de 14/10). Aparece junto da posição que a pessoa marcou com o tipo diferente do
da base (ADR 0005, seção 5): o aviso traz `posicao`, o índice da posição na lista enviada, e
`tipo`, o tipo usado. `{tipo}` é o `tipo` do aviso e `{tipo_marcado}` é o tipo que a pessoa marcou
naquela posição, os dois escritos com `avisos.tipo_corrigido.acao` ou `avisos.tipo_corrigido.fundo`.
