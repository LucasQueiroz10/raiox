# ADR 0004: Modelo IrRAE oficial, governança e execução

- **Status:** aceito (a lista de decisões conjuntas está como **proposta**, a confirmar pelo Lucas e pelo M1)
- **Data:** 2026-09-27
- **Decisores:** Lucas (Membro 2) e Membro 1

## Contexto

O IrRAE mede quanto do patrimônio de cada empresa está ligado a cada tema e subtema (por exemplo, Cadeia de IA › Nuvem e data centers). Existiam duas versões:

1. **Versão simples**, feita no repositório: média ponderada de 4 componentes com pesos fixos (0,30 · 0,20 · 0,35 · 0,15), no branch `feat/modelo-irrae`.
2. **Protótipo v1 do M1**, desenvolvido fora do repositório e entregue em zip: fusão de até 9 fontes com pesos pela precisão de cada fonte, resultado com faixa de incerteza (P5–P95), regras com histerese, selo pela largura da faixa, look-through de ETF com limites de dependência, 27 testes (segundo o guia do M1) e relatório técnico.

As duas versões tomavam decisões de metodologia em lugares diferentes (sessões separadas), o que gerou conflito (por exemplo, pesos fixos contra pesos por precisão).

## Decisões

### 1. Modelo oficial

O **protótipo v1 do M1** é o IrRAE oficial, na versão do arquivo `irrae_prototipo (1).zip` (26/09/2026, 00:13). A versão simples (`feat/modelo-irrae`) é descartada, sem integração.

### 2. Governança

| Papel | Dono | O que decide |
|---|---|---|
| **Metodologia** | **M1** | Fontes e componentes; precisões iniciais (kappa) e encolhimento; limiares e regras; taxonomia de temas e subtemas; mapeamentos segmento/capex/backlog → subtema; forma de apresentar o resultado |
| **Engenharia** | **Lucas** | Integração no repositório, testes, desempenho, dependências, execução em lote, armazenamento e segurança |

**Decisões conjuntas (proposta, a confirmar):** exigem a aprovação dos dois:
1. Qualquer número, rótulo ou faixa **novo que apareça na tela** para o usuário.
2. **Nova fonte de dados** no modelo (passa também pela `docs/matriz_de_dados.md`).
3. Mudança com efeito **regulatório ou jurídico**, como exibir exposição negativa ou o papel da empresa na cadeia.
4. Mudança que altere a **arquitetura ou o custo**: novas dependências pesadas, rodar fora do lote, dados pagos (por exemplo, preços para calibração).
5. **Ampliação da taxonomia** para além da Cadeia de IA.

**Uma única fonte da verdade:** toda a metodologia vive no repositório (configurações do modelo, código e ADRs). Mudanças entram só por pull request, com o CI verde. Zips e mensagens deixam de ser o canal de entrega.

### 3. Execução: em lote, no repositório

- O modelo roda **em lote**, fora da API: calcula o IrRAE de todas as empresas quando os dados mudam e grava o resultado no banco. A API **só lê** esse resultado.
- **Local no repositório:** `backend/ingest/irrae/` (código e configurações do modelo), com testes em `backend/tests/`.
- **Dependências científicas separadas** (`numpy`, `scipy`, `pandas`, `lxml`, `beautifulsoup4`, `requests`) num arquivo próprio, para a API continuar leve. Ferramentas de análise (`SALib` para Sobol, `matplotlib` para gráficos) ficam como dependências opcionais dos scripts de análise, fora do pipeline.
- **`float` e sorteios dentro do modelo** são permitidos. Na gravação, os pesos são convertidos para `Decimal` (truncados, sem passar de 100%). O motor da API continua exato (ver ADR 0003).
- **Reprodutibilidade:** cada execução grava a versão do modelo, a semente dos sorteios, a data dos dados e a versão das configurações.
- **Resultado gravado por empresa e subtema:** média, P5, P95, selo de precisão, origem e status de revisão. É o formato que a classificação e a agregação já esperam (`app/core/classificacao.py`), acrescido da faixa.

## Pontos em aberto (metodologia, com o M1)

Recomendações do M2 feitas na análise do protótipo, ainda sem decisão:

1. **Componente E (enquadramento por ETFs) fora do protótipo 1**, por causa da circularidade apontada pelo próprio M1 (o ETF analisado confirma o próprio rótulo) e do risco de parecer opinião sobre as empresas.
2. **Mapeamentos elicitados entram como rascunho** e só aparecem ao usuário com evidência registrada e revisão humana (regra do CLAUDE.md para conteúdo gerado com IA).
3. **Faixa na carteira pelo limite comonotônico** (soma dos quantis), chamada de "faixa estimada", e não de "intervalo de confiança".
4. **Exposição negativa fora da tela** no protótipo 1, até avaliação jurídica.
5. **Separar "núcleo" (sabemos que não é do tema) de "sem classificação" (não sabemos)** na agregação, seguindo o princípio "ausente ≠ zero" do modelo.
6. **Dados para o protótipo:** componentes A, Ir, B e N para 50 a 100 empresas americanas da cadeia de IA; R, C e P depois.

## Consequências

- O PR do `feat/modelo-irrae` deve ser fechado sem merge (ação no GitHub, pelo Lucas).
- O código do M1 será trazido num branch próprio, com os testes dele adaptados às convenções do projeto (encoding explícito, versões fixas, ruff). Antes, é preciso confirmar que as dependências instalam no Python 3.14 e que os testes passam.
- O banco precisa de uma tabela de resultados do IrRAE e do estado anterior de cada empresa (para a histerese dos limiares). Isso entra no ADR de banco e modelo de dados.
- As fontes usadas pelo protótipo que ainda não estão na matriz de dados (USPTO AI Patent Dataset, Financial Statement and Notes Data Sets da SEC, clientes relevantes no 10-K e preços para calibração) precisam ser acrescentadas e validadas pelo M1.
