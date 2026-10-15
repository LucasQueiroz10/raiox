"""Busca da PTAX com cache. O Banco Central é simulado: nenhum teste usa a internet."""

from datetime import date
from decimal import Decimal as D

import pytest

from app.dados.ptax import CambioIndisponivel, FontePtax, montar_url

HOJE = date(2026, 9, 28)  # segunda-feira


def resposta(*pares: tuple[str, float]) -> dict:
    return {"value": [{"cotacaoVenda": v, "dataHoraCotacao": f"{d} 13:00:00.0"} for d, v in pares]}


class BancoCentralFalso:
    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def __call__(self, inicio: date, fim: date) -> dict:
        self.chamadas.append((inicio, fim))
        r = self.respostas.pop(0) if len(self.respostas) > 1 else self.respostas[0]
        if isinstance(r, Exception):
            raise r
        return r


class Relogio:
    def __init__(self):
        self.segundos = 0.0

    def __call__(self) -> float:
        return self.segundos


def fonte(banco, relogio=None):
    return FontePtax(buscar=banco, hoje=lambda: HOJE, relogio=relogio or Relogio())


def test_busca_os_ultimos_15_dias_e_escolhe_a_cotacao_do_dia():
    banco = BancoCentralFalso(resposta(("2026-09-25", 5.40), ("2026-09-28", 5.42)))

    p = fonte(banco).cotacao()

    assert banco.chamadas == [(date(2026, 9, 13), HOJE)]
    assert (p.data_cotacao, p.valor, p.data_pedida) == (HOJE, D("5.42"), HOJE)


def test_antes_de_sair_a_ptax_do_dia_usa_a_do_dia_util_anterior():
    banco = BancoCentralFalso(resposta(("2026-09-25", 5.40)))

    assert fonte(banco).cotacao().data_cotacao == date(2026, 9, 25)


def test_dentro_de_uma_hora_usa_o_cache():
    banco = BancoCentralFalso(resposta(("2026-09-28", 5.42)))
    relogio = Relogio()
    f = fonte(banco, relogio)

    f.cotacao()
    relogio.segundos = 3599
    f.cotacao()

    assert len(banco.chamadas) == 1


def test_depois_de_uma_hora_busca_de_novo():
    banco = BancoCentralFalso(resposta(("2026-09-25", 5.40)), resposta(("2026-09-28", 5.42)))
    relogio = Relogio()
    f = fonte(banco, relogio)

    assert f.cotacao().data_cotacao == date(2026, 9, 25)
    relogio.segundos = 3601
    assert f.cotacao().data_cotacao == HOJE
    assert len(banco.chamadas) == 2


def test_banco_central_fora_do_ar_usa_a_ultima_cotacao_guardada():
    banco = BancoCentralFalso(resposta(("2026-09-25", 5.40)), OSError("fora do ar"))
    relogio = Relogio()
    f = fonte(banco, relogio)

    f.cotacao()
    relogio.segundos = 7200

    assert f.cotacao().valor == D("5.40")


def test_banco_central_fora_do_ar_sem_cache_da_erro_claro():
    with pytest.raises(CambioIndisponivel):
        fonte(BancoCentralFalso(OSError("fora do ar"))).cotacao()


def test_resposta_sem_cotacao_recente_da_erro_claro():
    with pytest.raises(CambioIndisponivel):
        fonte(BancoCentralFalso(resposta())).cotacao()


def test_url_aponta_para_a_api_ptax_do_banco_central_com_datas_no_formato_da_api():
    url = montar_url(date(2026, 9, 13), date(2026, 9, 28))

    assert url.startswith("https://olinda.bcb.gov.br/olinda/servico/PTAX/")
    assert "'09-13-2026'" in url and "'09-28-2026'" in url


def test_depois_de_uma_falha_so_tenta_de_novo_em_5_minutos():
    banco = BancoCentralFalso(resposta(("2026-09-25", 5.40)), OSError("fora do ar"))
    relogio = Relogio()
    f = fonte(banco, relogio)

    f.cotacao()  # busca 1: ok
    relogio.segundos = 3700
    f.cotacao()  # busca 2: falha, usa o cache
    relogio.segundos = 3700 + 299
    f.cotacao()  # ainda dentro dos 5 minutos: não tenta de novo

    assert len(banco.chamadas) == 2
    relogio.segundos = 3700 + 301
    f.cotacao()
    assert len(banco.chamadas) == 3


def test_cotacao_buscada_na_hora_tem_o_dia_da_busca_como_data_de_consulta():
    # Sem banco (desenvolvimento), a consulta ao Banco Central acontece na hora da análise.
    p = fonte(BancoCentralFalso(resposta(("2026-09-28", 5.4)))).cotacao()

    assert (p.data_cotacao, p.data_consulta) == (HOJE, HOJE)
