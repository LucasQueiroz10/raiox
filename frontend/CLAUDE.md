# Frontend — comandos e regras (rodar dentro de frontend/)

## Comandos
- npm ci
- npm run dev
- npm run test            Vitest
- npm run lint            ESLint
- npm run format:check    Prettier
- npm run typecheck       tsc --noEmit
- npm run gerar-tipos     openapi-typescript openapi.json -o src/api/tipos.ts
- npx playwright test     ponta a ponta
- npm audit --audit-level=high

## Regras
- src/api/tipos.ts é gerado; nunca editar à mão. Se a API mudar, regenerar e commitar.
- Textos de tela: copiados literalmente de docs/textos_telas.md para src/textos.ts,
  com a referência da seção. Nenhuma palavra alterada; nenhum texto solto nos componentes.
- A interface descreve exposição; nunca sugere comprar, vender ou rebalancear.
- Toda tela de resultado mostra a cobertura, a data das composições, o rótulo de aproximação
  UCITS e os créditos (GET /fontes).
- Números e datas formatados em pt-BR com Intl.
- No protótipo 1, a carteira não é persistida no navegador (ver "Fase atual" no CLAUDE.md da raiz).
- A carteira nunca é enviada a terceiros (nenhum serviço externo recebe posições ou valores).
- Sem analytics: nenhum script de rastreamento ou de métricas de terceiros no front.
