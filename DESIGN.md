---
name: Sagital
description: Vitrine do raio-x de carteira; quanto uma carteira depende, de fato, da cadeia de IA.
colors:
  laudo-noturno: "#0a1017"
  laudo-elevado: "#0f1822"
  linha-de-corte: "#1c2a36"
  linha-de-corte-forte: "#2a3f4f"
  texto-claro: "#e3ebf0"
  texto-suave: "#9cb0bd"
  ciano-de-contraste: "#6fd0e0"
  ambar-de-destaque: "#f2b544"
typography:
  display:
    fontFamily: "Schibsted Grotesk Variable, system-ui, sans-serif"
    fontSize: "clamp(2rem, 1.35rem + 2.2vw, 3.25rem)"
    fontWeight: 650
    lineHeight: 1.08
    letterSpacing: "-0.022em"
  headline:
    fontFamily: "Schibsted Grotesk Variable, system-ui, sans-serif"
    fontSize: "clamp(1.875rem, 1.4rem + 1.6vw, 2.5rem)"
    fontWeight: 650
    lineHeight: 1.08
  title:
    fontFamily: "Schibsted Grotesk Variable, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.012em"
  body:
    fontFamily: "Schibsted Grotesk Variable, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Schibsted Grotesk Variable, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  reto: "2px"
spacing:
  margem-celular: "16px"
  margem-desktop: "32px"
  bloco: "40px"
  secao: "64px"
components:
  serie:
    textColor: "{colors.texto-claro}"
    typography: "{typography.title}"
    padding: "18px 0"
  seletor-aba:
    textColor: "{colors.texto-suave}"
    height: "44px"
    padding: "0 14px"
  seletor-aba-atual:
    textColor: "{colors.texto-claro}"
  link:
    textColor: "{colors.ciano-de-contraste}"
---

# Design System: Sagital

## Overview

**Creative North Star: "A Sala de Laudo"**

A vitrine é lida como um exame de imagem numa sala de laudo: tela escura, luz baixa, o olhar
indo direto ao que a imagem mostra. A carteira é a imagem; cada camada do look-through
(carteira, fundos, empresas, exposição) é um corte que se separa para mostrar o que há dentro.
Tudo o que não é o corte ou o texto recua.

A densidade é baixa na moldura e calma na leitura. As cores se limitam a um fundo quase preto,
linhas finas e um ciano de contraste. Um âmbar fica reservado para o que mais importa num
resultado. Não há sombra, brilho, gradiente nem cartão: profundidade vem dos cortes em
perspectiva e das linhas.

Rejeições confirmadas pelo Lucas (10/11/2026): cara de corretora ou banco, de cripto e hype, de
artigo acadêmico e de template de startup.

**Key Characteristics:**
- Fundo de monitor de laudo, tema escuro como padrão.
- Linhas de 1px no lugar de caixas; listas como séries de exame, não cartões.
- Um único acento quente, raro.
- Uma animação assinada: os cortes que se separam.

## Colors

Fundo azul-marinho quase preto, neutros frios e um ciano de contraste; o âmbar é exceção.

### Primary
- **Ciano de contraste** (#6fd0e0): links, foco, a aba atual do seletor e os cortes da figura.
  Nos cortes, aparece translúcido (12% no preenchimento, 55% no traço); só a camada de exposição
  usa o ciano cheio, com a intensidade de cada célula.

### Secondary
- **Âmbar de destaque** (#f2b544): reservado ao número principal de exposição e à empresa que
  mais contribui. Ainda sem uso no esqueleto; entra com os números (PR 3).

### Neutral
- **Laudo noturno** (#0a1017): fundo de todas as páginas.
- **Laudo elevado** (#0f1822): fundo dos planos da figura e do atalho de teclado.
- **Linha de corte** (#1c2a36): divisórias entre linhas de lista, cabeçalho e rodapé.
- **Linha de corte forte** (#2a3f4f): abertura de listas, base do seletor, borda dos planos.
- **Texto claro** (#e3ebf0): títulos e texto principal (contraste de 15:1 sobre o fundo).
- **Texto suave** (#9cb0bd): subtítulos, descrições, avisos e rodapé (cerca de 8:1).

### Named Rules
**The One Voice Rule.** O âmbar aparece no máximo duas vezes por tela: o número principal e a
maior contribuição. Se aparecer num terceiro lugar, ele perde o sentido.

**The Cold Neutral Rule.** Neutros sempre frios, puxados do azul do fundo; texto secundário
nunca em cinza puro.

## Typography

**Display Font:** Schibsted Grotesk (variável, servida pelo site, com system-ui de reserva)
**Body Font:** Schibsted Grotesk
**Label/Mono Font:** Martian Mono, só para medidas, tickers e datas; entra com a primeira medida
na tela (PR 3).

**Character:** um grotesco de jornal, firme nos títulos e confortável no texto corrido; a mono
fica para o que é medida, nunca como fantasia de "técnico".

### Hierarchy
- **Display** (650, clamp 2rem a 3.25rem, 1.08): a pergunta do início e o nome da carteira;
  duas linhas no desktop, medida de 15em.
- **Headline** (650, clamp 1.875rem a 2.5rem, 1.08): títulos das páginas de leitura.
- **Title** (600, 1.5rem, 1.2): nome de cada carteira na lista de séries.
- **Body** (400, 1rem a 1.0625rem, 1.55 a 1.65): texto corrido, medida de 68ch nas páginas de
  leitura.
- **Label** (400 a 600, 0.8125rem a 1rem): avisos, legendas dos cortes, títulos de bloco e
  rodapé, sempre em caixa normal.

### Named Rules
**The No Kicker Rule.** Nenhum rótulo pequeno em caixa alta acima de título; o título se
sustenta sozinho.

## Layout

Coluna única no celular, com margem de 16px; a partir de 768px, margem de 32px. A largura
máxima é 1200px. No início, a partir de 960px, a pergunta ocupa a largura toda e o corpo se
divide em 5 e 7 frações (escolha à esquerda, figura à direita), com 64px entre as colunas.
Blocos se separam por 40px a 48px; páginas de leitura ficam numa coluna de 68ch. Todo alvo de
toque tem pelo menos 44px de altura.

## Elevation & Depth

Plano por padrão, sem sombra. A profundidade vem só dos cortes em perspectiva da figura
(rotateX 56° e rotateZ -34°) e das linhas de 1px.

### Named Rules
**The Flat Film Rule.** Nada flutua: sem sombra, brilho ou desfoque como decoração. O que tem
profundidade é a imagem, não a interface.

## Shapes

Cantos retos (2px) em tudo o que tem borda, inclusive o anel de foco. Divisórias horizontais de
1px; a aba atual do seletor ganha uma linha de 2px em ciano embaixo.

## Components

### Navigation
- **Cabeçalho:** marca à esquerda (símbolo do plano sagital, um círculo cortado por uma linha
  vertical em ciano, mais o nome), links à direita em texto suave; a página atual fica em texto
  claro. Altura de 64px, linha de 1px embaixo.
- **Seletor de carteiras:** abas de texto com 44px de altura; a atual em texto claro com a linha
  de 2px em ciano; quebra de linha no celular, sem rolagem lateral.

### Lista de séries
Cada carteira é uma linha: nome em title, descrição em texto suave, divisória de 1px. No
hover (só com mouse), o nome fica ciano e anda 4px para a direita; ao tocar, a linha encolhe
para 99%.

### Figura das camadas (assinatura)
Quatro cortes em perspectiva, do mais simples ao mais denso (uma posição, uma grade de fundos,
uma grade de empresas, a mesma grade com a intensidade da exposição), cada um com a legenda ao
lado. A pilha começa fechada e se abre uma vez ao entrar na tela (900ms, cubic-bezier(0.23, 1,
0.32, 1), 70ms entre cortes); as legendas entram 220ms depois. Com movimento reduzido, já aparece
aberta, sem transição.

## Do's and Don'ts

### Do:
- **Do** usar linhas de 1px (#1c2a36 e #2a3f4f) para separar, no lugar de caixas.
- **Do** manter o âmbar (#f2b544) só no número principal e na maior contribuição.
- **Do** tematizar seleção, foco (2px ciano, 3px de afastamento) e barra de rolagem com a paleta.
- **Do** servir as fontes pelo próprio site.

### Don't:
- **Don't** lembrar corretora ou banco: nada de verde e vermelho de cotação, nem painel de
  trading.
- **Don't** usar neon, brilho, gradiente ou energia de cripto.
- **Don't** montar a página com cartões iguais ou hero de template de startup.
- **Don't** pôr rótulo em caixa alta acima de título.
