# ADR 0003: Stack técnica do protótipo 1

- **Status:** aceito
- **Data:** 2026-09-26
- **Decisor:** Lucas (Membro 2)

## Contexto

O planejamento do MVP (24/09/2026) pede, na semana 1, um ADR de stack. As decisões abaixo já foram tomadas e estão em uso no repositório; este registro junta o que foi escolhido, por quê e o que ficou de fora. Hospedagem, banco de dados e o modelo IrRAE ficam em ADRs próprios.

## Decisões

### Backend

| Item | Escolha | Motivo |
|---|---|---|
| Linguagem | **Python 3.14** | O motor nasceu do tracker em Python. A versão 3.14 é a instalada na máquina de desenvolvimento, e as bibliotecas usadas já têm suporte a ela |
| Ambiente e dependências | **venv + pip**, com `requirements.txt` (produção) e `requirements-dev.txt` (ferramentas), versões fixas com `==` | Escolha do Lucas, sem ferramenta extra. `pyproject.toml` guarda só a configuração do ruff e do pytest |
| API | **FastAPI + Pydantic + uvicorn** | Validação de entrada tipada e OpenAPI gerado automaticamente, que alimenta os tipos do front |
| Motor (`app/core/`) | **Funções puras**, sem FastAPI, banco ou rede | Testável sem infraestrutura; o I/O fica em `app/api/` e em `ingest/` |
| Números | **`Decimal`**, nunca `float`, com 50 dígitos de precisão no look-through e na agregação; arredondamento só na saída da API | Dinheiro e pesos em cadeia perdem exatidão com `float`, e os 28 dígitos padrão do `Decimal` não bastam em cadeias de fundos |
| Identificador de empresa | **ISIN**, validado pelo dígito verificador; nunca SEDOL | Chave pública e global; SEDOL é propriedade da Bolsa de Londres |
| Testes | **pytest + Hypothesis** (propriedades), com teste escrito antes do código | Os testes são o critério para aceitar código, inclusive o gerado com IA |
| Qualidade | **ruff** (lint e formatação, com `yfinance` proibido por regra) e **pip-audit** | Uma ferramenta só para lint e formatação; auditoria de vulnerabilidades no CI |

### Frontend

| Item | Escolha | Motivo |
|---|---|---|
| Framework | **React 19 + TypeScript + Vite** | Stack prevista no plano e dominada pelas ferramentas de IA usadas no desenvolvimento |
| Versão do TypeScript | **6.0** (e não 7.0) | O `typescript-eslint` 8.x só aceita TypeScript abaixo de 6.1. Atualizar para o 7 vira um branch próprio quando o suporte existir |
| Testes | **Vitest + Testing Library (jsdom)** | Integrado ao Vite |
| Qualidade | **ESLint + Prettier**, `npm audit` | Padrão do ecossistema |
| Tipos da API | **Gerados do OpenAPI do FastAPI** (`openapi-typescript`), nunca editados à mão | Evita divergência entre front e back (a implementar em `chore/tipos-openapi`) |
| Node.js | **LTS (24)** | Versão de suporte longo, usada também no CI |

### Repositório, CI e segurança

| Item | Escolha | Motivo |
|---|---|---|
| Hospedagem do código | **GitHub**, repositório privado | Fluxo de PR e CI integrados |
| Fluxo | Branches curtos por tipo (`feat/`, `fix/`, `docs/`...), Conventional Commits em português, integração só por PR com CI verde | Histórico legível e revisão obrigatória |
| CI | **GitHub Actions**: workflows `backend`, `frontend` e `seguranca` em todo PR, com actions fixadas por hash e permissão só de leitura | Reprodutível e com superfície de ataque menor |
| Segredos | **gitleaks** no CI; `.env`, `.env.*` e `secrets/` no `.gitignore` e bloqueados para o Claude Code em `.claude/settings.json` | Nenhum segredo entra no histórico nem nas sessões de IA |
| Fim de linha | **LF**, forçado pelo `.gitattributes` | Desenvolvimento no Windows, CI no Linux |
| Desenvolvimento com IA | **Claude Code em sessão única**, sem subagentes | Regra do CLAUDE.md. O plano previa subagentes na semana 1; ver "Consequências" |

## Alternativas consideradas

- **uv** para ambiente e dependências (previsto no CLAUDE.md original): trocado por venv + pip por decisão do Lucas.
- **Python 3.12** (previsto no CLAUDE.md original): trocado pelo 3.14, a versão instalada.
- **TypeScript 7.0**: bloqueado pela compatibilidade do `typescript-eslint`.
- **`float` no motor**: descartado por perda de exatidão (ver "Números").
- **Páginas renderizadas no servidor** (citadas no plano como alternativa a React): não adotadas; React com tipos gerados da API mantém front e back desacoplados.
- **gitleaks-action**: trocada pela CLI do gitleaks, porque a action exige licença em contas de organização.

## Consequências

- O `Decimal` vale para o motor da API. O modelo IrRAE do M1, que usa sorteios Monte Carlo com `numpy`, deve rodar em lote fora da API e converter os pesos para `Decimal` na fronteira; isso será registrado no ADR do IrRAE.
- Bibliotecas científicas (`numpy`, `scipy`, `pandas`) entram, se aprovadas, num arquivo de dependências separado da API, para ela continuar leve.
- O plano do MVP prevê subagentes (escritor-de-testes e revisor-de-segurança). Enquanto a regra "sem subagentes" valer, esse item do plano fica suspenso e a revisão continua sendo feita pelo Lucas em cada PR.
- A proteção da `main` no GitHub gratuito não é aplicada em repositório privado. Até decidir entre o GitHub Pro e o fluxo por disciplina, nenhum push direto na `main` é feito pelo Claude, conforme o CLAUDE.md.
