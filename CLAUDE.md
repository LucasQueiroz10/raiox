# Projeto RX — Raio-X da Carteira
Protótipo web que mostra quanto da carteira está concentrado por empresa, setor, tema
e subtema, abrindo ETFs e fundos em cadeia (look-through) até as empresas.
Descreve exposição; nunca recomenda compra ou venda.

## Escopo do protótipo 1
Entra: cadastro manual; CSV da B3 e da Avenue; câmbio pela PTAX; raio-x por setor/tema/subtema;
empresas "escondidas"; cobertura da classificação; data de cada composição; rótulo de
aproximação nos ETFs UCITS; créditos às fontes; landing page com lista de espera.
Fora: contas, alertas, rentabilidade, cotações automáticas, IR, Open Finance, recomendações.

## Arquitetura
- backend/: Python 3.14, FastAPI, Pydantic; ambiente com venv + pip (requirements.txt).
  Ver backend/CLAUDE.md.
- frontend/: React + TypeScript + Vite sobre Node.js LTS. Ver frontend/CLAUDE.md.
- PostgreSQL: só dados públicos (composições por data, classificação versionada) e a lista
  de espera (e-mail, data, versão do aviso de privacidade). Carteiras NUNCA são gravadas:
  POST /raiox processa em memória e descarta.
- Rotas: POST /raiox, GET /fontes, POST /lista-espera, GET /saude.
- Fontes: CVM (CDA, ODbL, crédito obrigatório) e SEC (N-PORT). UCITS é aproximado pelo
  ETF americano do mesmo índice.
- Tipos do front gerados do OpenAPI do FastAPI (openapi-typescript); nunca editados à mão.

## Regras obrigatórias
- Teste primeiro. Nenhuma função do motor entra sem um teste que a descreva.
  Nunca altere um teste existente só para fazê-lo passar.
- A chave de empresa é o ISIN. Nunca use SEDOL.
- Use só fontes marcadas como permitidas em docs/matriz_de_dados.md.
- Nunca leia, crie ou altere .env, .env.* ou secrets/.
- Só dados sintéticos em código, testes, logs e conversa. Nada de nomes, e-mails ou carteiras reais.
- Os textos da interface vêm literalmente de docs/textos_telas.md.
- Classificação gerada por IA entra com status "rascunho".
- Uma tarefa por vez. Mudança em mais de um módulo exige um plano aprovado antes.
- Não use subagentes.

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
