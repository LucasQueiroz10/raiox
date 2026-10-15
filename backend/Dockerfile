# Imagem do backend (ADR 0007, seção 2): a API no Cloud Run e, com outro comando, as cargas e as
# migrações (Cloud Run Jobs). Comandos dentro de backend/:
#   docker build -t rx-backend .
#   scripts/testar_imagem.sh          constrói e testa como roda no Cloud Run (backend/CLAUDE.md)
#
# Só o que roda em produção: as dependências de produção (requirements.txt, sem as do lote nem as
# de desenvolvimento) e o código de app/, banco/ (migrações), cargas/ e ingest/ (os leitores da
# CVM). Ficam de fora tests/, irrae/ e medicoes/ (.dockerignore). Nenhum segredo entra na imagem:
# a configuração vem das variáveis de ambiente do Cloud Run (ADR 0007, seção 6).

# Python e Debian fixados pelo digest; o Dependabot propõe as atualizações (.github/dependabot.yml).
FROM python:3.14.8-slim-trixie@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170

# Sem buffer na saída, para os logs chegarem inteiros ao Cloud Logging mesmo se o job morrer.
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/opt/venv/bin:$PATH

# As dependências vão num ambiente virtual criado aqui, dentro da imagem, em /opt/venv. Não é o
# .venv do computador, que fica fora da imagem (.dockerignore): este nasce do zero em cada
# construção, separado do Python do sistema da imagem base, e o PATH acima o põe na frente.
# Só wheels prontas (--only-binary): nada é compilado na construção, e cada pacote confere com o
# hash do requirements.txt.
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
    && pip install --no-cache-dir --require-hashes --only-binary=:all: -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Usuário sem root e sem poder de escrita no código, que fica com o root.
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin rx

WORKDIR /app
COPY alembic.ini ./
COPY app/ app/
COPY banco/ banco/
COPY cargas/ cargas/
COPY ingest/ ingest/
# Compila agora: o usuário rx não escreve em /app, e a partida do contêiner fica mais rápida.
RUN python -m compileall -q app banco cargas ingest

USER rx
EXPOSE 8080

# A API. As cargas e as migrações usam a mesma imagem com outro comando, ex.:
# python -m cargas.cvm, python -m cargas.ptax ou python -m alembic upgrade head.
# --no-access-log: o Cloud Run já registra cada pedido; o log da aplicação não guarda IP.
# --no-proxy-headers: ignora o X-Forwarded-For, e o limite por IP usa o IP da conexão. A leitura do
# IP do cliente no Cloud Run vem antes do primeiro deploy (ADR 0007, seção 3). Nunca
# --forwarded-allow-ips="*" (backend/CLAUDE.md).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header", "--no-proxy-headers", "--no-access-log"]
