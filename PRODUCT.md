# Product

<!-- impeccable:product-schema 1 -->

Registro do produto para as skills de design. Fase atual: vitrine (ADR 0009). Confirmado pelo Lucas
em 10/11/2026, salvo o que está marcado como indecidido.

## Platform

web

## Users

Dois públicos, com o mesmo peso:

- **Investidor pessoa física curioso.** Tem ETF de índice ou ações de big techs e quer entender
  quanto do dinheiro depende, de fato, da cadeia de IA. Precisa de leitura didática, sem jargão, no
  celular.
- **Quem avalia o trabalho dos autores** (recrutadores, colegas, avaliadores técnicos). Quer ver o
  método, as fontes e a engenharia, a um clique da superfície.

Ninguém informa carteira: o visitante escolhe uma de três carteiras prontas.

## Product Purpose

Mostrar, em três carteiras públicas, quanto da exposição está na cadeia de IA, abrindo os ETFs até
as empresas (look-through) e medindo cada empresa pelo IrRAE, com uma faixa estimada.

Sucesso: o visitante entende a diferença entre "parece uma empresa de IA" e "depende da cadeia de
IA", e consegue conferir de onde vem cada número.

## Positioning

- Exposição fundamental por componentes (A, Ir, B, R, N, C, P e prior setorial), e não um rótulo
  binário "é ou não é de IA".
- Incerteza explícita: média e faixa P5 a P95 por Monte Carlo (2.000 sorteios, semente fixa).
- Look-through até a empresa, com cobertura, data e fonte pública em todo resultado.

## Operating Context

- Site estático. Os resultados vêm de snapshots JSON gerados em lote no backend; não há servidor de
  cálculo.
- Carteiras: `big-techs` (NVIDIA, Amazon, Apple e Microsoft, 25% cada); `sp500` (IVV, pelo N-PORT
  da SEC, cerca de 60 dias de defasagem); `ibovespa` (BOVA11, pelo CDA da CVM, cerca de 1 mês).
- Rotas: `/`, `/carteira/:id`, `/carteira/:id/empresa/:empresaId`, `/metodologia`, `/fontes`.
- Especificação completa: `docs/vitrine/especificacao.md`.

## Capabilities and Constraints

- Descreve exposição; nunca recomenda. Nada de "compre", "venda", "reduza", "aumente", "ideal" ou
  "melhor carteira" (recomendação exige registro na CVM, Resolução CVM 19/2021).
- O termo é "faixa estimada", nunca "intervalo de confiança", "IC90" ou "conservadora".
- Sem entrada de dados, conta, e-mail, cookies, analytics nem scripts de terceiros. O navegador não
  faz requisição a outro domínio: fontes tipográficas e arquivos são servidos pelo próprio site.
- Textos de tela vêm literalmente de `docs/textos_telas.md`; só os aprovados entram na interface.
- Sem logos de empresas, índices, bolsas ou órgãos; só nomes e tickers em texto.
- Números em pt-BR: vírgula decimal, `%` colado, faixa entre colchetes com travessão curto
  (`69% [56–81]`).
- Indecididos (ADR 0009, seção 5): faixa da carteira com um ou dois cenários (V-09, M1); snapshots
  com dados reais (V-01); licença ODbL do snapshot (V-03); corte de cobertura (V-04); hospedagem e
  domínio (V-07).

## Brand Commitments

- Nome: Sagital, sempre no feminino ("a Sagital").
- Projeto sem fins comerciais, de autoria do Lucas e do M1.
- Identidade sugerida na especificação (seção 7), não fechada: base escura de exame de imagem,
  ciano, um único acento quente; evitar roxo, laranja e preto com amarelo.

## Evidence on Hand

- Ainda não há número real do IrRAE. Até a V-01, só dados sintéticos com a faixa "Dados
  ilustrativos". Nunca inventar números para empresas reais nem copiar os do relatório técnico.
- Método: `docs/irrae/especificacao_v1.1.md`, `docs/decisoes_m1_irrae_v1.1.md` e
  `docs/irrae/relatorio_tecnico_v1.pdf` (este ainda descreve a v1, DT-8).
- Não há depoimentos, clientes nem métricas de uso.

## Product Principles

1. Mostrar, não recomendar.
2. Incerteza à vista: toda estimativa vem com faixa, cobertura e data.
3. Rastreável: cada número leva a uma fonte pública.
4. Didático na superfície, completo um clique abaixo.
5. Nada é recebido do visitante.

## Accessibility & Inclusion

Contraste WCAG AA, celular primeiro, navegação por teclado, nada transmitido só por cor (a faixa
também aparece em texto), áreas de toque de 44 px ou mais e respeito a `prefers-reduced-motion`.
