#!/usr/bin/env bash
# Testa a imagem do backend (Dockerfile; ADR 0007) como ela roda no Cloud Run:
#   1. conteúdo: usuário sem root, sem escrita no código, sem tests/, irrae/ e medicoes/ e sem as
#      dependências do lote e de desenvolvimento; os comandos das três cargas abrem;
#   2. migrações (python -m alembic upgrade head), como rx_dono;
#   3. carga da CVM com um zip sintético (python -m cargas.cvm --zip), como rx_ingestao;
#   4. a API em produção (o comando da imagem), como rx_api, lendo o que a carga publicou, e o IP
#      do limite tirado do X-Forwarded-For pela aplicação (RX_PROXIES_CONFIAVEIS; DT-17).
#
# Uso, dentro de backend/, com o Docker aberto e o venv ativo (o python do computador gera o zip
# sintético com tests/ingest/cda_sintetico.py e confere as respostas da API):
#   scripts/testar_imagem.sh            constrói a imagem rx-backend:teste e testa
#   scripts/testar_imagem.sh IMAGEM     testa uma imagem já construída
#
# O banco é um PostgreSQL descartável (a imagem fixada do compose.yaml) numa rede própria, sem porta
# no computador: o banco de desenvolvimento não é tocado. Tudo é apagado no fim, mesmo com erro.
# Só dados sintéticos.
set -euo pipefail

# Git Bash no Windows: não trocar os caminhos de dentro do contêiner (/tmp/...) por caminhos do
# Windows. Nenhum caminho do computador é passado ao docker.
export MSYS_NO_PATHCONV=1

cd "$(dirname "$0")/.."

IMAGEM="${1:-}"
if [[ -z "$IMAGEM" ]]; then
    IMAGEM=rx-backend:teste
    docker build -t "$IMAGEM" .
fi

REDE="rx-imagem-$$"
BANCO="rx-imagem-banco-$$"
API="rx-imagem-api-$$"
SEGREDO="segredo-sintetico-do-teste-da-imagem-$$"  # o do aquecimento, que abre a medição do IP

limpar() {
    docker rm -f "$API" "$BANCO" >/dev/null 2>&1 || true
    docker network rm "$REDE" >/dev/null 2>&1 || true
}
trap limpar EXIT

passo() { echo "==> $*"; }

# rodar USUARIO COMANDO...: roda a imagem na rede do banco, conectada ao banco rx como USUARIO.
rodar() {
    local usuario="$1"
    shift
    docker run --rm -i --network "$REDE" \
        -e RX_BANCO_URL="postgresql+psycopg://$usuario@$BANCO:5432/rx" "$IMAGEM" "$@"
}

passo "Conteúdo da imagem"
docker run --rm -i "$IMAGEM" python - <<'PY'
import importlib.util
import os
from pathlib import Path

assert os.getuid() != 0, "a imagem roda como root"
assert not os.access("app", os.W_OK), "o usuário da imagem consegue alterar o código"
fora = [p for p in ("tests", "irrae", "medicoes", ".venv") if Path(p).exists()]
assert not fora, f"pastas que não deviam estar na imagem: {fora}"
# Só o requirements.txt: nada do lote (pandas, lxml, numpy) nem de desenvolvimento.
extras = [m for m in ("pandas", "lxml", "numpy", "pytest", "hypothesis") if importlib.util.find_spec(m)]
assert not extras, f"dependências que não são de produção: {extras}"
PY
for carga in cvm cadastro ptax; do
    docker run --rm "$IMAGEM" python -m "cargas.$carga" --help >/dev/null
done

passo "PostgreSQL descartável"
docker network create "$REDE" >/dev/null
docker run -d --name "$BANCO" --network "$REDE" -e POSTGRES_HOST_AUTH_METHOD=trust \
    "$(docker compose config --images)" >/dev/null
# Pelo TCP: durante a inicialização, o servidor temporário do PostgreSQL só aceita o soquete local.
for _ in $(seq 60); do
    docker exec "$BANCO" pg_isready -q -h 127.0.0.1 -U postgres && break
    sleep 1
done
docker exec "$BANCO" pg_isready -q -h 127.0.0.1 -U postgres

passo "Usuários e banco (banco.preparar: só no teste; em produção, passo manual do ADR 0007)"
docker run --rm --network "$REDE" \
    -e RX_BANCO_URL_ADMIN="postgresql+psycopg://postgres@$BANCO:5432/postgres" \
    "$IMAGEM" python -m banco.preparar

passo "Migrações, como rx_dono"
rodar rx_dono python -m alembic upgrade head
atual="$(rodar rx_dono python -m alembic current)"
if [[ "$atual" != *"(head)"* ]]; then
    echo "as migrações não chegaram ao fim: $atual"
    exit 1
fi

passo "Carga da CVM com zip sintético, como rx_ingestao"
python - <<'PY' | rodar rx_ingestao sh -c \
    'cat > /tmp/cda_fi_202608.zip && exec python -m cargas.cvm --zip /tmp/cda_fi_202608.zip'
import sys

from tests.ficticios import cnpj, isin
from tests.ingest.cda_sintetico import MesSintetico

fundo = cnpj("IMAGEM-FUNDO")
mes = MesSintetico("202608").patrimonio(fundo, "1000.00")
mes.aplicacao("fi_BLC_4", fundo, "Ações", "1000.00", CD_ISIN=isin("IMAGEM-ACAO"))
sys.stdout.buffer.write(mes.zip().getvalue())
PY

passo "API em produção, como rx_api"
docker run -d --name "$API" --network "$REDE" -p 127.0.0.1::8080 \
    -e RX_AMBIENTE=producao -e RX_BANCO_URL="postgresql+psycopg://rx_api@$BANCO:5432/rx" \
    -e RX_PROXIES_CONFIAVEIS=2 -e RX_SEGREDO_AQUECIMENTO="$SEGREDO" \
    "$IMAGEM" >/dev/null
RX_API="http://$(docker port "$API" 8080/tcp | head -n 1)" RX_SEGREDO="$SEGREDO" python - <<'PY' || {
import json
import os
import time
import urllib.error
import urllib.request
from decimal import Decimal

from tests.ficticios import cnpj, isin

API = os.environ["RX_API"]


def pedir(caminho, corpo=None, cabecalhos=None):
    dados = None if corpo is None else json.dumps(corpo).encode()
    cabecalhos = {"Content-Type": "application/json", **(cabecalhos or {})}
    pedido = urllib.request.Request(API + caminho, data=dados, headers=cabecalhos)
    try:
        with urllib.request.urlopen(pedido, timeout=10) as resposta:
            return resposta.status, resposta.headers, json.load(resposta)
    except urllib.error.HTTPError as erro:
        return erro.code, erro.headers, None


for _ in range(30):
    try:
        status, cabecalhos, _ = pedir("/api/saude")
        break
    except OSError:  # o servidor ainda está subindo
        time.sleep(1)
else:
    raise SystemExit("a API não respondeu em 30 s")
assert status == 200, status
assert "server" not in cabecalhos, "--no-server-header"
assert "strict-transport-security" in cabecalhos, "RX_AMBIENTE=producao liga o HSTS"
assert pedir("/openapi.json")[0] == 404, "RX_AMBIENTE=producao desliga a documentação"

# O fundo da carga, pelo CNPJ: a API abre a composição que a carga publicou no banco.
fundo, acao = cnpj("IMAGEM-FUNDO"), isin("IMAGEM-ACAO")
posicao = {
    "tipo_identificador": "cnpj",
    "identificador": fundo,
    "valor": "1000.00",
    "moeda": "BRL",
    "tipo": "fundo",
}
status, _, raiox = pedir("/api/raiox", {"posicoes": [posicao]})
assert status == 200, status
fundos = [(f["fundo_id"], f["data_referencia"]) for f in raiox["fundos"]]
assert fundos == [(f"CNPJ:{fundo}", "2026-08-31")], fundos
empresas = [(e["empresa_id"], Decimal(e["via_fundos"])) for e in raiox["empresas"]]
assert empresas == [(acao, Decimal(1000))], empresas

# DT-17: o uvicorn (--no-proxy-headers) deixa o X-Forwarded-For para a aplicação, que usa o
# penúltimo endereço com RX_PROXIES_CONFIAVEIS=2. IPs dos blocos reservados para documentação.
medir = {
    "x-forwarded-for": "198.51.100.7, 203.0.113.5, 192.0.2.30",
    "x-rx-aquecimento": os.environ["RX_SEGREDO"],
}
status, _, medicao = pedir("/interno/ip-do-cliente", cabecalhos=medir)
assert status == 200, status
assert medicao["chave_do_limite"] == "203.0.113.5", medicao
PY
    docker logs "$API"
    exit 1
}
# O Cloud Run já registra cada pedido, com o IP; o log da aplicação não (--no-access-log).
if docker logs "$API" 2>&1 | grep -qE "/(api|interno)/"; then
    echo "o log da API registrou pedidos (falta --no-access-log)"
    exit 1
fi

passo "Imagem ok: $IMAGEM"
