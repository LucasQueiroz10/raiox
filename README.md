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
[ API FastAPI ]  POST /raiox · GET /fontes · POST /lista-espera · GET /saude
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
├── backend/        API, motor do raio-x, rotinas de ingestão e testes (Python)
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
- PostgreSQL (local ou em contêiner)

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
python -m pytest -q
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