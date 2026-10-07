"""POST /raiox: recebe a carteira, calcula em memória e devolve o raio-x.

Nada da carteira é gravado nem registrado em log.
"""

from decimal import ROUND_HALF_UP, Decimal
from functools import cache

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api import esquemas as e
from app.api.seguranca import LimitadorPorJanela, LimiteDeAnalises, ServidorOcupado
from app.core.agregacao import NUCLEO, Fatia, RaioX, agregar
from app.core.cambio import PtaxUsada, para_reais
from app.core.composicao import Categoria, Posicao, TipoItem
from app.core.lookthrough import abrir_carteira
from app.dados.exemplo import RepositorioExemplo
from app.dados.ptax import CambioIndisponivel, FontePtax
from app.dados.repositorio import RepositorioDados

router = APIRouter()

MAX_EMPRESAS_NA_RESPOSTA = 200  # as maiores da carteira; o resto vai somado em demais_empresas
ANALISES_POR_MINUTO = 20  # por IP
MAX_ANALISES_SIMULTANEAS = 4  # por servidor
_CENTAVOS = Decimal("0.01")
_QUATRO_CASAS = Decimal("0.0001")


@cache
def obter_repositorio() -> RepositorioDados:
    # Até o banco existir, a API usa o conjunto de exemplo sintético.
    return RepositorioExemplo()


@cache
def obter_fonte_ptax() -> FontePtax:
    return FontePtax()


@cache
def obter_limitador_raiox() -> LimitadorPorJanela:
    return LimitadorPorJanela(ANALISES_POR_MINUTO, 60)


@cache
def obter_limite_de_analises() -> LimiteDeAnalises:
    return LimiteDeAnalises(MAX_ANALISES_SIMULTANEAS)


def verificar_taxa(
    request: Request,
    limitador: LimitadorPorJanela = Depends(obter_limitador_raiox),  # noqa: B008 - padrão do FastAPI
) -> None:
    """Conta toda chamada ao /raiox, inclusive as que vão dar 422."""
    ip = request.client.host if request.client else "sem-ip"
    if not limitador.permitir(ip):
        raise HTTPException(
            429,
            detail={"codigo": "muitas_analises"},
            headers={"Retry-After": str(limitador.espera(ip))},
        )


def _reais(valor: Decimal) -> Decimal:
    return valor.quantize(_CENTAVOS, rounding=ROUND_HALF_UP)


def _fracao(valor: Decimal) -> Decimal:
    return valor.quantize(_QUATRO_CASAS, rounding=ROUND_HALF_UP)


def _categoria(chave: object) -> e.CategoriaFatia:
    if chave is None:
        return "sem_classificacao"
    if chave == NUCLEO:
        return "nucleo"
    return "classificado"


def _fatias(fatias: dict[object, Fatia]) -> list[e.Fatia]:
    return [
        e.Fatia(
            nome=None if chave is None or chave == NUCLEO else str(chave),
            categoria=_categoria(chave),
            valor=_reais(f.valor),
            percentual=_fracao(f.percentual),
            valor_preliminar=_reais(f.valor_preliminar),
        )
        for chave, f in sorted(fatias.items(), key=lambda item: -item[1].valor)
    ]


def _subtemas(fatias: dict[object, Fatia]) -> list[e.FatiaSubtema]:
    saida = []
    for chave, f in sorted(fatias.items(), key=lambda item: -item[1].valor):
        tema, subtema = chave if isinstance(chave, tuple) else (None, None)
        saida.append(
            e.FatiaSubtema(
                tema=tema,
                nome=subtema,
                categoria=_categoria(chave),
                valor=_reais(f.valor),
                percentual=_fracao(f.percentual),
                valor_preliminar=_reais(f.valor_preliminar),
            )
        )
    return saida


def _montar_resposta(
    raio_x: RaioX,
    categorias: dict[Categoria, Decimal],
    fundos: list[e.Fundo],
    avisos: list[e.Aviso],
    repo: RepositorioDados,
    ptax: PtaxUsada | None,
) -> e.RaioXResposta:
    c = raio_x.cobertura
    exibidas = raio_x.empresas[:MAX_EMPRESAS_NA_RESPOSTA]
    demais = raio_x.empresas[MAX_EMPRESAS_NA_RESPOSTA:]
    valor_demais = sum((emp.total for emp in demais), Decimal(0))
    return e.RaioXResposta(
        total=_reais(raio_x.total),
        versao_classificacao=raio_x.versao_classificacao,
        ptax=(
            e.Ptax(valor=ptax.valor, data_cotacao=ptax.data_cotacao, data_pedida=ptax.data_pedida)
            if ptax
            else None
        ),
        cobertura=e.Cobertura(
            total_acoes=_reais(c.total_acoes),
            confirmada=_reais(c.confirmada),
            preliminar=_reais(c.preliminar),
            sem_classificacao=_reais(c.sem_classificacao),
            percentual_confirmada=_fracao(c.percentual_confirmada),
            percentual_preliminar=_fracao(c.percentual_preliminar),
            percentual_classificada=_fracao(c.percentual_classificada),
        ),
        por_setor=_fatias(raio_x.por_setor),
        por_tema=_fatias(raio_x.por_tema),
        por_subtema=_subtemas(raio_x.por_subtema),
        categorias={cat.value: _reais(v) for cat, v in categorias.items()},
        derivativos_por_setor=_fatias(raio_x.derivativos_por_setor),
        credito_por_setor=_fatias(raio_x.credito_por_setor),
        vendido_por_setor=_fatias(raio_x.vendido_por_setor),
        empresas=[
            e.Empresa(
                isin=emp.empresa_id,
                nome=repo.nome(emp.empresa_id),
                setor=emp.setor,
                selo_setor=emp.selo_setor.value if emp.selo_setor else None,
                temas=[
                    e.Tema(tema=t.tema, subtema=t.subtema, peso=_fracao(t.peso), selo=t.selo.value)
                    for t in emp.temas
                ],
                direto=_reais(emp.direto),
                via_fundos=_reais(emp.via_fundos),
                total=_reais(emp.total),
                percentual=_fracao(emp.percentual),
                escondida=emp.escondida,
                fundos=sorted(emp.fundos),
            )
            for emp in exibidas
        ],
        demais_empresas=e.DemaisEmpresas(
            quantidade=len(demais),
            valor=_reais(valor_demais),
            percentual=_fracao(valor_demais / raio_x.total) if raio_x.total else Decimal(0),
        ),
        fundos=fundos,
        avisos=avisos,
    )


@router.post("/raiox", response_model=e.RaioXResposta, dependencies=[Depends(verificar_taxa)])
def raiox(
    entrada: e.EntradaRaioX,
    repo: RepositorioDados = Depends(obter_repositorio),  # noqa: B008 - padrão do FastAPI
    fonte_ptax: FontePtax = Depends(obter_fonte_ptax),  # noqa: B008 - padrão do FastAPI
    limite: LimiteDeAnalises = Depends(obter_limite_de_analises),  # noqa: B008 - padrão do FastAPI
) -> e.RaioXResposta:
    ptax = None
    if any(p.moeda == "USD" for p in entrada.posicoes):
        try:
            ptax = fonte_ptax.cotacao()
        except CambioIndisponivel as erro:
            raise HTTPException(503, detail={"codigo": "cambio_indisponivel"}) from erro

    try:
        with limite.vaga():
            return _analisar(entrada, repo, ptax)
    except ServidorOcupado as erro:
        raise HTTPException(
            503, detail={"codigo": "servidor_ocupado"}, headers={"Retry-After": "2"}
        ) from erro


def _analisar(
    entrada: e.EntradaRaioX, repo: RepositorioDados, ptax: PtaxUsada | None
) -> e.RaioXResposta:
    posicoes = [
        Posicao(p.isin, para_reais(p.valor, p.moeda, ptax), TipoItem(p.tipo))
        for p in entrada.posicoes
    ]
    resultado = abrir_carteira(posicoes, repo.composicoes())
    raio_x = agregar(resultado, repo.tabela_classificacao())

    fundos = [
        e.Fundo(
            isin=f.fundo_id,
            nome=repo.nome(f.fundo_id),
            data_referencia=f.data_referencia,
            fonte=f.fonte,
            aproximado_por=f.aproximado_por,
            valor_recebido=_reais(f.valor_recebido),
            pesos={cat.value: _fracao(p) for cat, p in f.pesos.items()},
        )
        for f in sorted(resultado.fundos.values(), key=lambda f: f.fundo_id)
    ]
    avisos = [
        e.Aviso(codigo=a.codigo.value, fundo_isin=a.fundo_id)
        for a in sorted(resultado.avisos, key=lambda a: (a.codigo, a.fundo_id or ""))
    ]
    return _montar_resposta(raio_x, resultado.categorias, fundos, avisos, repo, ptax)
