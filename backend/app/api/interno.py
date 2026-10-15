"""Endpoints internos: aquecimento e medição do X-Forwarded-For (ADR 0007, seção 3).

Ficam fora do /api, então o Firebase não os encaminha (a exceção é a medição, só no primeiro
deploy: ADR 0007, seção 2); como o endereço run.app é público, exigem o segredo do aquecimento no
cabeçalho e respondem 404 sem ele, como se não existissem.

- POST /interno/aquecer: o Cloud Scheduler chama depois da carga diária da CDA, para nenhum
  usuário pagar a releitura dos dados. Relê dentro do próprio pedido (no Cloud Run não há CPU fora
  dos pedidos) e não devolve dados.
- GET /interno/ip-do-cliente (DT-17): no primeiro deploy, o Lucas chama uma vez pelo domínio e
  outra direto ao run.app, para ver em que posição do X-Forwarded-For o IP dele chega e acertar
  RX_PROXIES_CONFIAVEIS. Devolve os endereços só para quem chamou e não os registra em log; no ADR
  vão só as posições, nunca os IPs. Temporário: sai num PR próprio depois da medição
  (docs/runbooks/producao.md, seção 3, passo 5).
"""

import hmac

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.api.seguranca import chave_do_limite, enderecos_do_xff

CABECALHO_AQUECIMENTO = "x-rx-aquecimento"

router = APIRouter(include_in_schema=False)


def _autorizado(request: Request) -> bool:
    esperado = request.app.state.segredo_aquecimento
    recebido = request.headers.get(CABECALHO_AQUECIMENTO)
    if not esperado or not recebido:
        return False
    return hmac.compare_digest(recebido.encode(), esperado.encode())


@router.post("/interno/aquecer", status_code=204)
def aquecer(request: Request) -> Response:
    if not _autorizado(request):
        raise HTTPException(404)
    if not request.app.state.dados.aquecer():
        raise HTTPException(503, detail={"codigo": "dados_indisponiveis"})
    return Response(status_code=204)


class MedicaoIp(BaseModel):
    x_forwarded_for: list[str]  # os endereços na ordem em que chegaram, da esquerda para a direita
    proxies_confiaveis: int
    chave_do_limite: str


@router.get("/interno/ip-do-cliente")
def ip_do_cliente(request: Request) -> MedicaoIp:
    if not _autorizado(request):
        raise HTTPException(404)
    cabecalhos = request.headers.getlist("x-forwarded-for")
    proxies = request.app.state.proxies_confiaveis
    return MedicaoIp(
        x_forwarded_for=enderecos_do_xff(cabecalhos),
        proxies_confiaveis=proxies,
        chave_do_limite=chave_do_limite(
            cabecalhos, request.client.host if request.client else None, proxies
        ),
    )
