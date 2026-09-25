from decimal import Decimal as D

import pytest

from app.core.classificacao import (
    Classificacao,
    Origem,
    ParticipacaoTema,
    Selo,
    Status,
)
from tests.ficticios import isin

CADEIA_IA = "Cadeia de IA"


def nuvem(peso: str, **extra) -> ParticipacaoTema:
    return ParticipacaoTema(CADEIA_IA, "Nuvem", D(peso), **extra)


def test_o_que_sobra_dos_temas_fica_no_nucleo():
    c = Classificacao(
        isin("VAREJODIG"),
        setor="Varejo digital",
        temas=(nuvem("0.35"), ParticipacaoTema(CADEIA_IA, "Modelos", D("0.10"))),
    )

    assert c.peso_nucleo == D("0.55")


def test_empresa_sem_tema_fica_inteira_no_nucleo():
    c = Classificacao(isin("BANCO"), setor="Financeiro")

    assert c.peso_nucleo == 1


def test_pesos_dos_temas_nao_podem_passar_de_100_por_cento():
    with pytest.raises(ValueError):
        Classificacao(isin("X"), setor="Tecnologia", temas=(nuvem("0.7"), nuvem("0.4")))


@pytest.mark.parametrize("peso", ["0", "-0.1"])
def test_peso_de_tema_precisa_ser_positivo(peso):
    with pytest.raises(ValueError):
        Classificacao(isin("X"), setor="Tecnologia", temas=(nuvem(peso),))


def test_origem_oficial_e_manual_entram_aprovadas_e_confirmadas():
    oficial = Classificacao(isin("A"), setor="Financeiro", setor_origem=Origem.OFICIAL)
    manual = Classificacao(isin("B"), setor="Financeiro", setor_origem=Origem.MANUAL)

    assert oficial.setor_status is Status.APROVADO
    assert oficial.selo_setor is Selo.CONFIRMADA
    assert manual.selo_setor is Selo.CONFIRMADA


@pytest.mark.parametrize("origem", [Origem.WIKIDATA, Origem.IA, Origem.MODELO_IRRAE])
def test_origens_nao_revisadas_entram_como_rascunho_e_preliminar(origem):
    c = Classificacao(isin("A"), setor="Tecnologia", setor_origem=origem)
    tema = nuvem("0.3", origem=origem)

    assert c.setor_status is Status.RASCUNHO
    assert c.selo_setor is Selo.PRELIMINAR
    assert tema.status is Status.RASCUNHO
    assert tema.selo is Selo.PRELIMINAR


def test_rascunho_revisado_vira_confirmado():
    tema = nuvem("0.3", origem=Origem.IA, status=Status.APROVADO)

    assert tema.selo is Selo.CONFIRMADA
