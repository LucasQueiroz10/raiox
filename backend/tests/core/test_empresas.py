"""Classes da mesma empresa somam numa empresa só (ADR 0005, DT-3).

O ativo_id identifica o que está na carteira ou no fundo; o empresa_id, quem emitiu. A tabela
ativo -> empresa vem dos dados; item de fundo sem ativo (ex.: ação no N-PORT, sem ticker) aponta
direto para a empresa.
"""

from datetime import date
from decimal import Decimal as D
from decimal import localcontext

from hypothesis import given, settings

from app.core.agregacao import agregar
from app.core.classificacao import Classificacao, ParticipacaoTema, TabelaClassificacao
from app.core.composicao import Composicao, ItemComposicao, Posicao, TipoItem
from app.core.lookthrough import PRECISAO, abrir_carteira
from tests.core.test_lookthrough_propriedades import ACOES, composicoes, posicoes, quase_igual
from tests.ficticios import isin

PN, ON = isin("EMPXPN"), isin("EMPXON")  # duas classes de ação da mesma empresa
EMPRESA = "ZZ:EMPX"
ETF = isin("ETFEMP")
EMPRESA_DO_ATIVO = {PN: EMPRESA, ON: EMPRESA}


def fundo(*itens: ItemComposicao) -> dict[str, Composicao]:
    return {ETF: Composicao(ETF, date(2026, 8, 31), "teste", itens)}


def test_classes_da_mesma_empresa_somam_numa_empresa_so():
    carteira = [Posicao(PN, D("600"), TipoItem.ACAO), Posicao(ON, D("400"), TipoItem.ACAO)]

    r = abrir_carteira(carteira, {}, empresa_do_ativo=EMPRESA_DO_ATIVO)

    assert list(r.empresas) == [EMPRESA]
    e = r.empresas[EMPRESA]
    assert (e.direto, e.via_fundos) == (D("1000"), D("0"))
    assert e.por_ativo == {PN: D("600"), ON: D("400")}


def test_uma_classe_direta_e_outra_via_fundo_marcam_a_empresa_como_escondida():
    carteira = [Posicao(ON, D("300"), TipoItem.ACAO), Posicao(ETF, D("1000"), TipoItem.FUNDO)]
    fundos = fundo(ItemComposicao(PN, D("0.5"), TipoItem.ACAO))

    r = abrir_carteira(carteira, fundos, empresa_do_ativo=EMPRESA_DO_ATIVO)

    e = r.empresas[EMPRESA]
    assert (e.direto, e.via_fundos, e.fundos) == (D("300"), D("500"), {ETF})
    assert e.por_ativo == {ON: D("300"), PN: D("500")}


def test_item_de_fundo_sem_ativo_aponta_direto_para_a_empresa():
    # Caso do N-PORT: a posição do ETF vem só com a empresa (pelo LEI), sem ticker.
    carteira = [Posicao(PN, D("200"), TipoItem.ACAO), Posicao(ETF, D("1000"), TipoItem.FUNDO)]
    fundos = fundo(ItemComposicao(None, D("0.4"), TipoItem.ACAO, empresa_id=EMPRESA))

    r = abrir_carteira(carteira, fundos, empresa_do_ativo=EMPRESA_DO_ATIVO)

    assert list(r.empresas) == [EMPRESA]
    e = r.empresas[EMPRESA]
    assert (e.direto, e.via_fundos) == (D("200"), D("400"))
    assert e.por_ativo == {PN: D("200"), None: D("400")}


def test_ativo_sem_empresa_conhecida_vira_a_propria_empresa():
    desconhecido = isin("SEMEMPRESA")

    r = abrir_carteira([Posicao(desconhecido, D("100"), TipoItem.ACAO)], {}, empresa_do_ativo={})

    assert r.empresas[desconhecido].por_ativo == {desconhecido: D("100")}


def test_vendido_de_uma_classe_vai_para_a_empresa_e_nao_para_as_classes_compradas():
    fundos = fundo(
        ItemComposicao(PN, D("0.5"), TipoItem.ACAO), ItemComposicao(ON, D("-0.1"), TipoItem.ACAO)
    )

    r = abrir_carteira(
        [Posicao(ETF, D("1000"), TipoItem.FUNDO)], fundos, empresa_do_ativo=EMPRESA_DO_ATIVO
    )

    e = r.empresas[EMPRESA]
    assert (e.via_fundos, e.vendido) == (D("500"), D("-100"))
    assert e.por_ativo == {PN: D("500")}


def test_derivativo_soma_pela_empresa_do_ativo_objeto():
    fundos = fundo(ItemComposicao(None, D("0.03"), TipoItem.DERIVATIVO, ativo_objeto=PN))

    r = abrir_carteira(
        [Posicao(ETF, D("1000"), TipoItem.FUNDO)], fundos, empresa_do_ativo=EMPRESA_DO_ATIVO
    )

    assert r.derivativos_por_empresa == {EMPRESA: D("30")}


def test_raio_x_mostra_a_empresa_uma_vez_com_a_parte_de_cada_classe():
    carteira = [Posicao(PN, D("600"), TipoItem.ACAO), Posicao(ON, D("400"), TipoItem.ACAO)]
    nuvem = ParticipacaoTema("Cadeia de IA", "Nuvem", D("0.25"))
    tabela = TabelaClassificacao(
        "teste", {EMPRESA: Classificacao(EMPRESA, "Tecnologia", temas=(nuvem,))}
    )

    r = agregar(abrir_carteira(carteira, {}, empresa_do_ativo=EMPRESA_DO_ATIVO), tabela)

    (e,) = r.empresas
    assert (e.empresa_id, e.total, e.setor) == (EMPRESA, D("1000"), "Tecnologia")
    assert [(c.ativo_id, c.valor, c.percentual_da_empresa) for c in e.classes] == [
        (PN, D("600"), D("0.6")),
        (ON, D("400"), D("0.4")),
    ]
    assert r.por_setor["Tecnologia"].valor == D("1000")
    assert r.por_tema["Cadeia de IA"].valor == D("250")


@settings(deadline=None)
@given(posicoes, composicoes)
def test_juntar_classes_nao_muda_os_totais(carteira, fundos):
    # Liga as ações sintéticas a duas empresas: a junção só muda o agrupamento, nunca os valores.
    ligacao = {ACOES[0]: "ZZ:EMPA", ACOES[1]: "ZZ:EMPA", ACOES[2]: "ZZ:EMPB"}

    separado = abrir_carteira(carteira, fundos, max_passos=5000)
    junto = abrir_carteira(carteira, fundos, max_passos=5000, empresa_do_ativo=ligacao)

    assert junto.categorias == separado.categorias
    with localcontext(prec=PRECISAO):  # mesma precisão do look-through
        for campo in ("direto", "via_fundos", "vendido", "credito"):
            a = sum((getattr(e, campo) for e in separado.empresas.values()), D(0))
            b = sum((getattr(e, campo) for e in junto.empresas.values()), D(0))
            assert quase_igual(a, b), campo
        for e in junto.empresas.values():
            assert quase_igual(sum(e.por_ativo.values(), D(0)), e.total)
        assert quase_igual(
            sum(separado.derivativos_por_empresa.values(), D(0)),
            sum(junto.derivativos_por_empresa.values(), D(0)),
        )
    assert not set(ligacao) & set(junto.derivativos_por_empresa)
