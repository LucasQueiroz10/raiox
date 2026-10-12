# Projeto RX · Raio-X da Carteira

Descubra onde seu dinheiro realmente está.

O Projeto RX abre os ETFs e fundos da carteira do investidor até chegar às empresas (*look-through*) e mostra quanto do patrimônio está concentrado no mesmo setor, tema ou empresa, inclusive quando essa concentração está escondida em vários fundos diferentes.

> **Status:** em desenvolvimento. Protótipo 1 previsto para novembro de 2026.

> **Aviso:** o Projeto RX é uma ferramenta de informação sobre a carteira do próprio usuário. Ele descreve a exposição e **não faz recomendação** de investimento.

## Funcionalidades do protótipo 1

- Cadastro manual da carteira ou importação de CSV (B3 e Avenue)
- Conversão de valores em dólar pela PTAX do dia
- Raio-x por setor, tema e subtema (ex.: cadeia de IA)
- Lista de empresas "escondidas" dentro dos fundos
- Indicador de cobertura da classificação e data de cada composição
- Aproximação rotulada para ETFs UCITS
- Landing page com lista de espera

Ficam para versões seguintes: contas de usuário, alertas de concentração, rentabilidade e cotações automáticas.

## Stack

| Camada | Tecnologias |
|---|---|
| Back-end | Python 3.14, FastAPI, Pydantic, venv + pip |
| Front-end | React, TypeScript, Vite, Node.js LTS |
| Banco | PostgreSQL |
| Testes | pytest, Hypothesis, Vitest, Playwright |
| Qualidade e segurança | ruff, ESLint, Prettier, pip-audit, npm audit, gitleaks |
| CI | GitHub Actions |

## Arquitetura

```
[ Navegador ]  React + TypeScript
      │  JSON (tipos gerados do OpenAPI)
      ▼
[ API FastAPI ]  POST /api/raiox · GET /api/fontes · POST /api/lista-espera · GET /api/saude
      │
      ▼
[ Motor (core) ]  importação → câmbio → look-through → classificação → agregação
      │
      ▼
[ PostgreSQL ]  composições dos fundos por data e tabela de classificação versionada
      ▲
[ Rotinas de ingestão ]  CVM (mensal) e SEC (trimestral)
```

No protótipo atual, a carteira do usuário é processada em memória e não é gravada. O único dado pessoal armazenado é o e-mail de quem entra na lista de espera. Contas de usuário com carteiras salvas, criptografadas, estão previstas para uma próxima versão.

## Estrutura do repositório

```
projeto-rx/
├── backend/        API, motor do raio-x, rotinas de ingestão, migrações do banco e testes (Python)
├── frontend/       landing page e telas do produto (React + TypeScript)
├── docs/           ADRs, matriz de dados, textos das telas e runbooks
├── .github/        workflows de CI
├── .claude/        configuração do Claude Code
└── CLAUDE.md       instruções do projeto para o Claude Code
```

## Como rodar localmente

### Pré-requisitos
- [Git](https://git-scm.com/downloads/win) (no Windows, com Git Bash)
- [Python 3.14](https://www.python.org/downloads/)
- [Node.js LTS](https://nodejs.org)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para o PostgreSQL do projeto)

### Back-end
```bash
cd backend
cp .env.example .env                           # preencha as variáveis
py -3.14 -m venv .venv                         # cria o ambiente (uma vez)
source .venv/Scripts/activate                  # Git Bash no Windows; no Linux: .venv/bin/activate
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```
A documentação interativa da API fica em `http://localhost:8000/docs`.

### Banco de dados
O PostgreSQL de desenvolvimento roda no Docker, só em `127.0.0.1:5433`. A primeira vez:
```bash
cd backend
docker compose up -d --wait
export RX_BANCO_URL_ADMIN=postgresql+psycopg://postgres@127.0.0.1:5433/postgres
python -m banco.preparar                       # cria os usuários e o banco rx
export RX_BANCO_URL=postgresql+psycopg://rx_dono@127.0.0.1:5433/rx
python -m alembic upgrade head                 # aplica as migrações
```
Para a API ler o banco, suba o `uvicorn` com
`RX_BANCO_URL=postgresql+psycopg://rx_api@127.0.0.1:5433/rx`. Sem essa variável, ela usa o
conjunto de exemplo sintético.
Os detalhes estão em `backend/CLAUDE.md` e no ADR 0006.

### Front-end
```bash
cd frontend
npm install
npm run gerar-tipos         # gera src/api/tipos.ts a partir do OpenAPI
npm run dev
```

## Testes e qualidade

```bash
# back-end
cd backend
source .venv/Scripts/activate
python -m pytest -q        # os testes com banco pedem RX_BANCO_TESTE_URL (ver backend/CLAUDE.md)
python -m ruff check .

# front-end
cd frontend
npm test
npm run lint
```

O CI roda testes, lint e varreduras de segurança em todo pull request.

## Fluxo de trabalho com Git

- `main` é protegida: toda mudança entra por pull request, depois do CI verde e de revisão.
- Os branches têm prefixo por tipo: `feat/`, `fix/`, `test/`, `docs/`, `chore/`, `refactor/`.
- Os commits seguem o [Conventional Commits](https://www.conventionalcommits.org/pt-br/), em português.
  Exemplo: `feat(core): abre fundos em cadeia com proteção contra ciclos`

## Fontes de dados

| Fonte | Uso | Licença |
|---|---|---|
| CVM, Dados Abertos (CDA, FII, cadastro de companhias) | Composição de fundos e ETFs brasileiros | ODbL. Fonte: CVM, dados abertos |
| SEC, Form N-PORT | Composição de ETFs americanos | Domínio público |
| Banco Central do Brasil (PTAX) | Câmbio | Dados abertos do BC |

As composições têm defasagem: a da CVM é mensal e a dos ETFs americanos é trimestral. A data de cada uma aparece na tela.

## Privacidade

O projeto segue a LGPD: coleta o mínimo necessário, não guarda carteiras e mantém os registros de acesso por 6 meses, sem dados de carteira. Nenhum dado pessoal real é usado em código, testes ou logs.

## Licença

Código proprietário. Todos os direitos reservados.