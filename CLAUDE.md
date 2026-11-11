# Projeto RX — Raio-X da Carteira
Protótipo web que mostra quanto da carteira está concentrado por empresa, setor, tema
e subtema, abrindo ETFs e fundos em cadeia (look-through) até as empresas.
Descreve exposição; nunca recomenda compra ou venda.

## Fase atual: vitrine (ADR 0009)
O produto está arquivado desde 10/11/2026 (tag produto-arquivado-2026-11); o roteiro para
retomar está no ADR 0009, seção 4. O código do produto continua na main e no CI, mas não é
publicado: nada de deploy, cargas agendadas, lista de espera nem importação de CSV.
A vitrine é um site estático, sem fins comerciais, do Lucas e do M1, com a marca Sagital. O
visitante escolhe uma de três carteiras públicas (big-techs, sp500 pelo IVV, ibovespa pelo BOVA11)
e vê o raio-x dela com o IrRAE. Especificação: docs/vitrine/especificacao.md.
Dados:
- O visitante não envia nada: sem carteira, ticker, arquivo, conta ou e-mail. Nenhum dado pessoal.
- Os resultados vêm de snapshots JSON gerados em lote no backend; o navegador não chama a API
  nem serviços externos.
- Sem números de IrRAE com dados reais até a decisão V-01; até lá, snapshots sintéticos com a
  faixa "Dados ilustrativos".
Estas regras só mudam com decisão registrada em ADR em docs/adr/.

## Arquitetura
- backend/: Python 3.14, FastAPI, Pydantic; ambiente com venv + pip (requirements.txt).
  Ver backend/CLAUDE.md.
- frontend/: React + TypeScript + Vite sobre Node.js LTS. Ver frontend/CLAUDE.md.
- PostgreSQL: dados públicos (composições por data, classificação versionada) e a lista
  de espera (e-mail, data, versão do aviso de privacidade). O que pode ou não ser
  gravado sobre carteiras depende da fase: ver "Fase atual: protótipo 1" neste arquivo.
- Rotas, todas sob /api (o Firebase repassa o caminho inteiro; ADR 0007): POST /api/raiox,
  GET /api/fontes, POST /api/lista-espera, GET /api/saude.
- Fontes: CVM (CDA, ODbL, crédito obrigatório) e SEC (N-PORT). UCITS é aproximado pelo
  ETF americano do mesmo índice.
- Tipos do front gerados do OpenAPI do FastAPI (openapi-typescript); nunca editados à mão.
  O tipo do snapshot da vitrine é gerado do JSON Schema exportado pelo backend (ADR 0009).

## Regras obrigatórias
- Teste primeiro. Nenhuma função do motor entra sem um teste que a descreva.
  Nunca altere um teste existente só para fazê-lo passar.
- Ativos são identificados pelo `ativo_id` e empresas pelo `empresa_id` (ADR 0005).
  Nunca guarde CUSIP, SEDOL nem ISIN de país fora da lista permitida do ADR 0005.
- Use só fontes marcadas como permitidas em docs/matriz_de_dados.md.
- Nunca leia, crie ou altere .env, .env.* ou secrets/.
- Só dados sintéticos em código, testes, logs e conversa. Nada de nomes, e-mails ou carteiras reais.
- Arquivos de escritório (.xlsx, .xls, .docx, .doc, .pptx) não entram no repositório: os metadados guardam o nome de quem editou. O conteúdo vira .md, com a fonte (ex.: "planilha do M1") e a data da versão transcrita no topo, sem nome de pessoa; fórmula que importa para a metodologia vira texto no .md ou código com teste. Exceção: outro binário só entra com os metadados removidos (PDF sem autor, imagem sem EXIF).
- Os textos da interface vêm literalmente de docs/textos_telas.md.
- Classificação gerada por IA entra com status "rascunho".
- Uma tarefa por vez. Mudança em mais de um módulo exige um plano aprovado antes.
- Não use subagentes.
- Limitações aceitas e pendências técnicas ficam em docs/divida_tecnica.md (itens DT-n).
  Leia antes de mexer num módulo; ao criar uma limitação nova, registre lá e marque o código
  com um comentário "DT-n"; ao resolver, apague o item no mesmo PR.

## Git
- main protegida; nada de commit direto nela. Branches curtos a partir da main:
  feat/, fix/, test/, docs/, chore/, refactor/.
- Um commit pequeno a cada passo verde, em Conventional Commits e em português.
  Ex.: "feat(core): abre fundos em cadeia com proteção contra ciclos".
- Antes de cada commit: testes e lint da parte alterada e conferir que nenhum segredo entrou no diff.
- Integração só por PR, depois do CI verde e da revisão do Lucas.
- Proibido sem pedido explícito: push, merge na main, rebase de branch publicado, force push.

## Ambiente
Windows com Git Bash; o CI roda em Linux. Fim de linha LF (garantido pelo .gitattributes).
Caminhos sempre com pathlib; todo arquivo aberto com encoding explícito.
