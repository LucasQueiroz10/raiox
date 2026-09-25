# ADR 0001: Hash de senha com Argon2id

- **Status:** aceito
- **Data:** 2026-09-25
- **Decisor:** Lucas (Membro 2)

## Contexto

O protótipo 1 não tem contas de usuário nem login (está na lista do que fica fora do escopo). O único dado pessoal gravado é o e-mail da lista de espera, sem senha.

Quando o projeto for além do protótipo e passar a ter login, as senhas precisarão ser guardadas com um hash próprio para senhas, lento e resistente a ataques com GPU.

## Decisão

Quando houver login, as senhas serão guardadas com **Argon2id**.

- Biblioteca: `argon2-cffi` (`argon2.PasswordHasher`).
- Parâmetros: no mínimo os recomendados pela OWASP no momento da implementação, revisados antes de entrar em produção.
- A verificação usa `PasswordHasher.verify` e, quando `check_needs_rehash` indicar, o hash é refeito com os parâmetros atuais no próximo login.

## Alternativas consideradas

- **bcrypt:** amplamente usado, mas limita a senha a 72 bytes e não permite ajustar o uso de memória.
- **PBKDF2:** aceito em contextos com exigência de FIPS, mas barato de atacar com GPU.
- **scrypt:** resistente a GPU, mas com menos suporte e parâmetros menos padronizados que o Argon2id.

## Consequências

- Nada muda no protótipo 1: não há senhas para guardar.
- Incluir login é uma mudança de escopo e exige revisar o aviso de privacidade (Membro 1) e atualizar o CLAUDE.md antes da implementação.
