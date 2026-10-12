"""Trava de passos do look-through (DT-4): limita o tempo de uma análise.

Com a trava padrão, uma carteira de até uns 33 ETFs globais (9.000 ações cada) abre inteira; acima
disso, o que falta abrir vira "não aberto", com o aviso limite_de_processamento. Cada item aberto é
um passo: a posição, mais os 9.000 itens e o caixa de cada ETF.
"""

from datetime import date
from decimal import Decimal as D

from app.core.composicao import Categoria, Composicao, ItemComposicao, Posicao, TipoItem
from app.core.identificadores import digito_verificador
from app.core.lookthrough import MAX_PASSOS, Aviso, CodigoAviso, abrir_carteira

ACOES_POR_ETF = 9_000
PASSOS_POR_ETF = 1 + ACOES_POR_ETF + 1  # a posição, as ações e o caixa


def _isin(corpo: str) -> str:
    return corpo + digito_verificador(corpo)


ETF = _isin("ZZETFGLOBAL")
ETF_GLOBAL = Composicao(
    ETF,
    date(2026, 8, 31),
    "fonte sintética",
    (
        *(
            ItemComposicao(_isin(f"ZZA{n:08d}"), D("0.99") / ACOES_POR_ETF, TipoItem.ACAO)
            for n in range(ACOES_POR_ETF)
        ),
        ItemComposicao(None, D("0.01"), TipoItem.CAIXA),
    ),
)


def _carteira(etfs: int) -> list[Posicao]:
    return [Posicao(ETF, D("1000"), TipoItem.FUNDO) for _ in range(etfs)]


def test_trava_padrao_cobre_ate_33_etfs_globais():
    # Abaixo da trava a carteira abre inteira, como em todos os outros testes do motor.
    assert MAX_PASSOS == 300_000
    assert 33 * PASSOS_POR_ETF <= MAX_PASSOS < 34 * PASSOS_POR_ETF


def test_acima_da_trava_o_resto_vira_nao_aberto_com_aviso():
    r = abrir_carteira(_carteira(34), {ETF: ETF_GLOBAL})

    assert Aviso(CodigoAviso.LIMITE_DE_PROCESSAMENTO, None) in r.avisos
    assert r.categorias[Categoria.NAO_ABERTO] > 0
    assert sum(r.categorias.values()) == r.total  # nada some: o que não abriu fica à vista
