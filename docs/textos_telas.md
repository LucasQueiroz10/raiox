# Textos das telas

Fonte única de todos os textos da interface do Projeto RX.

## Regras

- O front copia cada texto **literalmente** para `frontend/src/textos.ts`, sem mudar nenhuma palavra, acento ou pontuação.
- Só textos com status **aprovado** entram no código. Textos em **rascunho** ou **a escrever** não aparecem na interface.
- Os textos descrevem a exposição da carteira e **nunca recomendam** compra, venda ou rebalanceamento.
- Toda mudança em um texto aprovado volta para **rascunho** e passa por nova revisão (Membro 1).
- Cada texto tem um identificador (`tela.nome`) que o código usa para encontrá-lo.
- Trechos entre chaves, como `{data}`, são preenchidos pelo sistema com o valor da análise.

Status possíveis: `a escrever` · `rascunho` · `aprovado`

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

Quando aparecem as notas:

- `raiox.nota_cobertura`: sempre junto do indicador de cobertura.
- `raiox.nota_derivativos`: sempre que o total em derivativos da carteira for diferente de zero.
- `raiox.nota_posicoes_vendidas`: sempre que o total em posições vendidas for diferente de zero. O texto deve seguir a linha da nota de derivativos, explicando que a identificação da exposição é limitada.

## Avisos comuns

| Identificador | Texto | Status |
|---|---|---|
| `avisos.nao_e_recomendacao` | Este raio-x descreve a sua carteira. Não é recomendação de compra, venda ou de qualquer mudança nos seus investimentos. | rascunho |
| `avisos.creditos_fontes` | Fontes: CVM, dados abertos (licença ODbL); SEC, Estados Unidos; Banco Central do Brasil (PTAX). | rascunho |
| `avisos.ciclo` | Alguns fundos investem uns nos outros em círculo. Seguimos esse caminho até o valor ficar abaixo de 0,1% e mostramos o restante como não aberto. | rascunho |
| `avisos.fundo_sem_composicao` | Não encontramos a composição de um dos seus fundos. O valor dele aparece como não aberto. | rascunho |

## Avisos e erros da API

Um texto para cada código que a API devolve (`avisos[].codigo` e `detail.codigo`).

| Identificador | Texto | Status |
|---|---|---|
| `avisos.ciclo_sem_convergencia` | Um dos seus fundos entra num círculo de investimentos que não fecha. O valor que circula aparece como não aberto. | rascunho |
| `avisos.cadeia_longa` | Um dos seus fundos investe em uma cadeia muito longa de outros fundos. A parte mais distante aparece como não aberta. | rascunho |
| `avisos.limite_de_processamento` | Esta carteira é grande demais para abrir por completo. A parte que não deu para abrir aparece como não aberta. | rascunho |
| `erros.entrada_invalida` | Alguns dados da carteira não estão no formato esperado. Confira os campos marcados. | rascunho |
| `erros.corpo_grande_demais` | A carteira enviada é grande demais. Divida em partes menores. | rascunho |
| `erros.muitas_analises` | Você fez muitas análises em pouco tempo. Tente de novo em alguns instantes. | rascunho |
| `erros.servidor_ocupado` | Estamos com muitas análises ao mesmo tempo. Tente de novo em alguns instantes. | rascunho |
| `erros.cambio_indisponivel` | Não conseguimos a cotação do dólar agora. Tente de novo mais tarde ou informe os valores em reais. | rascunho |
| `erros.erro_interno` | Algo deu errado do nosso lado. Tente de novo em alguns instantes. | rascunho |
