"""Limitador por janela deslizante e limite de análises simultâneas (sem HTTP, relógio simulado)."""

import pytest

from app.api.seguranca import LimitadorPorJanela, LimiteDeAnalises, ServidorOcupado


class Relogio:
    def __init__(self):
        self.segundos = 0.0

    def __call__(self) -> float:
        return self.segundos


def test_permite_ate_o_limite_na_janela_e_recusa_o_seguinte():
    lim = LimitadorPorJanela(3, 60, relogio=Relogio())

    assert [lim.permitir("ip-a") for _ in range(4)] == [True, True, True, False]


def test_libera_quando_a_chamada_mais_antiga_sai_da_janela():
    relogio = Relogio()
    lim = LimitadorPorJanela(2, 60, relogio=relogio)
    lim.permitir("ip-a")  # t = 0
    relogio.segundos = 10
    lim.permitir("ip-a")

    relogio.segundos = 59.9
    assert not lim.permitir("ip-a")
    assert lim.espera("ip-a") == 1  # a chamada de t = 0 sai da janela em 0,1 s

    relogio.segundos = 60
    assert lim.permitir("ip-a")


def test_chamada_recusada_nao_conta():
    relogio = Relogio()
    lim = LimitadorPorJanela(1, 60, relogio=relogio)
    lim.permitir("ip-a")
    relogio.segundos = 30
    lim.permitir("ip-a")  # recusada

    relogio.segundos = 60
    assert lim.permitir("ip-a")


def test_cada_ip_tem_sua_propria_conta():
    lim = LimitadorPorJanela(1, 60, relogio=Relogio())

    assert lim.permitir("ip-a")
    assert lim.permitir("ip-b")
    assert not lim.permitir("ip-a")
    assert lim.espera("ip-b") == 60


def test_ips_inativos_sao_esquecidos_para_a_memoria_nao_crescer():
    relogio = Relogio()
    lim = LimitadorPorJanela(5, 60, relogio=relogio, limpar_acima_de=2)
    lim.permitir("ip-a")
    lim.permitir("ip-b")

    relogio.segundos = 61
    lim.permitir("ip-c")

    assert len(lim) == 1


def test_no_maximo_n_analises_ao_mesmo_tempo():
    lim = LimiteDeAnalises(2)

    with lim.vaga(), lim.vaga(), pytest.raises(ServidorOcupado), lim.vaga():
        pass
    with lim.vaga():  # as vagas voltaram
        pass


def test_vaga_e_devolvida_mesmo_quando_a_analise_falha():
    lim = LimiteDeAnalises(1)

    with pytest.raises(RuntimeError), lim.vaga():
        raise RuntimeError("falha simulada")
    with lim.vaga():
        pass
