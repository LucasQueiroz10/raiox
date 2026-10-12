"""Endpoint interno de aquecimento (ADR 0007, seção 3).

O Cloud Scheduler chama POST /interno/aquecer depois da carga diária da CDA, para nenhum usuário
pagar a releitura dos dados. Fica fora do /api, então o Firebase não o encaminha; como o endereço
run.app é público, exige o segredo no cabeçalho e responde 404 sem ele, como se não existisse. Relê
dentro do próprio pedido (no Cloud Run não há CPU fora dos pedidos) e não devolve dados.
"""

import hmac

from fastapi import APIRouter, HTTPException, Request, Response

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
