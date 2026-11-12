---
version: 1
slug: "frontend-src-app-tsx"
primary_target: "frontend/src/App.tsx"
related_targets: []
---

# Vitrine da Sagital: moldura do site

Escopo: todas as rotas da vitrine (início, raio-x da carteira, empresa, como medimos, fontes).
Modo: Read (o visitante quer entender quanto uma carteira depende da cadeia de IA), com o início
fazendo a escolha da carteira.

Público: investidor pessoa física curioso e quem avalia o trabalho dos autores, com o mesmo peso.
Tarefa: escolher uma das três carteiras, ver a exposição com faixa estimada e conferir fonte e data.
Restrições: textos literais de docs/textos_telas.md; nada recebido do visitante; nenhuma requisição
a outro domínio; WCAG AA; celular primeiro. Evitar: cara de corretora, de cripto, de artigo
acadêmico e de template de startup (resposta do Lucas, 10/11/2026).

Momento memorável: a abertura em camadas (resposta do Lucas, 10/11/2026).

Indecidido: tema claro (opcional na especificação); a faixa da carteira (V-09).

Para o PR 3 (primeiras figuras com dados): as anotações nos quatro cantos (carteira, data de
referência, fonte, data do cálculo), a Martian Mono nas medidas e o acento âmbar no número
principal e na maior contribuição.

## Direction contract

THESIS: A vitrine é uma sala de leitura de exame de imagem. A carteira é a imagem, e cada camada
(carteira, fundos, empresas, exposição) é um corte que se separa para mostrar o que há dentro.
Recusa o painel de corretora (cotações, verde e vermelho) e o hero de startup com três cartões.

OWN-WORLD: fundo azul-marinho quase preto, como monitor de laudo; cortes e linhas em ciano de baixa
saturação, finos, sem brilho nem gradiente; um único acento âmbar, só no número principal e na
maior contribuição; Schibsted Grotesk em títulos e texto; Martian Mono só em medidas, tickers,
datas e anotações de canto; anotações nos quatro cantos das figuras, como num visualizador de
imagem; cantos retos.

STORY: o visitante entende que um ETF é uma pilha de empresas, escolhe uma carteira, lê a exposição
com faixa e confere de onde veio cada número.

FIRST VIEWPORT: no desktop, a pergunta em duas linhas e o subtítulo na largura toda; embaixo, à
esquerda (5 de 12 colunas) o aviso e a lista das três carteiras como séries de um exame (nome
grande, descrição); à direita (7 colunas) a pilha dos quatro cortes em perspectiva, cada um
anotado com o nome e a frase da camada. No celular: pergunta, lista, pilha com cada corte na sua
linha. (Revisado em 10/11/2026: numa coluna de 5/12, a pergunta quebrava em sete linhas.)

FORM: mundo próprio fixado pela especificação (seção 7), posição 1 de 1. Assinatura: os cortes se
separam uma vez quando a figura entra na tela; com movimento reduzido, já aparecem separados.
seed: none (direção fixada pelo Lucas)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
