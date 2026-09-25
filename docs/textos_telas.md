# Textos das telas

Fonte única de todos os textos da interface do Projeto RX.

## Regras

- O front copia cada texto **literalmente** para `frontend/src/textos.ts`, sem mudar nenhuma palavra, acento ou pontuação.
- Só textos com status **aprovado** entram no código. Textos em **rascunho** ou **a escrever** não aparecem na interface.
- Os textos descrevem a exposição da carteira e **nunca recomendam** compra, venda ou rebalanceamento.
- Toda mudança em um texto aprovado volta para **rascunho** e passa por nova revisão (Membro 1).
- Cada texto tem um identificador (`tela.nome`) que o código usa para encontrá-lo.

Status possíveis: `a escrever` · `rascunho` · `aprovado`

---

## Landing

| Identificador | Texto | Status |
|---|---|---|
| `landing.titulo` | | a escrever |
| `landing.subtitulo` | | a escrever |
| `landing.lista_espera.chamada` | | a escrever |
| `landing.lista_espera.campo_email` | | a escrever |
| `landing.lista_espera.botao` | | a escrever |
| `landing.lista_espera.sucesso` | | a escrever |
| `landing.lista_espera.erro` | | a escrever |
| `landing.aviso_privacidade` | | a escrever |

## Cadastro

| Identificador | Texto | Status |
|---|---|---|
| `cadastro.titulo` | | a escrever |
| `cadastro.manual.instrucao` | | a escrever |
| `cadastro.csv.instrucao` | | a escrever |
| `cadastro.csv.b3` | | a escrever |
| `cadastro.csv.avenue` | | a escrever |
| `cadastro.erro.formato` | | a escrever |
| `cadastro.aviso_nao_gravamos` | | a escrever |

## Câmbio

| Identificador | Texto | Status |
|---|---|---|
| `cambio.titulo` | | a escrever |
| `cambio.ptax_usada` | | a escrever |
| `cambio.dia_util_anterior` | | a escrever |

## Raio-X

| Identificador | Texto | Status |
|---|---|---|
| `raiox.titulo` | | a escrever |
| `raiox.por_setor` | | a escrever |
| `raiox.por_tema` | | a escrever |
| `raiox.por_subtema` | | a escrever |
| `raiox.empresas_escondidas.titulo` | | a escrever |
| `raiox.empresas_escondidas.explicacao` | | a escrever |
| `raiox.cobertura` | | a escrever |
| `raiox.data_composicao` | | a escrever |
| `raiox.rotulo_ucits` | | a escrever |
| `raiox.caixa` | | a escrever |
| `raiox.credito` | | a escrever |
| `raiox.titulos_publicos` | | a escrever |
| `raiox.nao_identificado` | | a escrever |
| `raiox.nao_aberto` | | a escrever |
| `raiox.nota_derivativos` | NOTA: A dinâmica financeira do contrato de derivativos nao permite quantificar com precisão a exposição ao mercado, logo esse número representa apenas a % investida nesse mecanismo | rascunho |
| `raiox.nota_posicoes_vendidas` | | a escrever |

Quando aparecem as notas:

- `raiox.nota_derivativos`: sempre que o total em derivativos da carteira for diferente de zero.
- `raiox.nota_posicoes_vendidas`: sempre que o total em posições vendidas for diferente de zero. O texto deve seguir a linha da nota de derivativos, explicando que a identificação da exposição é limitada.

## Avisos comuns

| Identificador | Texto | Status |
|---|---|---|
| `avisos.nao_e_recomendacao` | | a escrever |
| `avisos.creditos_fontes` | | a escrever |
| `avisos.ciclo` | | a escrever |
| `avisos.fundo_sem_composicao` | | a escrever |
