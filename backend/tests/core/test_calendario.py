from datetime import date, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.core.calendario import dia_util, feriados, pascoa, ultimo_dia_util

anos = st.integers(min_value=1900, max_value=2200)
dias = st.dates(min_value=date(1900, 1, 10), max_value=date(2200, 12, 31))


@pytest.mark.parametrize(
    "esperada",
    [
        date(2000, 4, 23),
        date(2019, 4, 21),
        date(2024, 3, 31),
        date(2025, 4, 20),
        date(2026, 4, 5),
        date(2038, 4, 25),  # data mais tardia possível
        date(2285, 3, 22),  # data mais cedo possível
    ],
)
def test_pascoa_em_anos_conhecidos(esperada):
    assert pascoa(esperada.year) == esperada


def test_feriados_de_2026():
    assert feriados(2026) == {
        date(2026, 1, 1),  # Confraternização Universal
        date(2026, 2, 16),  # Carnaval (segunda)
        date(2026, 2, 17),  # Carnaval (terça)
        date(2026, 4, 3),  # Sexta-feira Santa
        date(2026, 4, 21),  # Tiradentes
        date(2026, 5, 1),  # Dia do Trabalho
        date(2026, 6, 4),  # Corpus Christi
        date(2026, 9, 7),  # Independência
        date(2026, 10, 12),  # Nossa Senhora Aparecida
        date(2026, 11, 2),  # Finados
        date(2026, 11, 15),  # Proclamação da República
        date(2026, 11, 20),  # Consciência Negra
        date(2026, 12, 25),  # Natal
    }


def test_consciencia_negra_so_e_feriado_nacional_a_partir_de_2024():
    # Lei 14.759/2023.
    assert date(2023, 11, 20) not in feriados(2023)
    assert date(2024, 11, 20) in feriados(2024)


@pytest.mark.parametrize(
    ("dia", "esperado"),
    [
        (date(2026, 9, 24), True),  # quinta comum
        (date(2026, 9, 26), False),  # sábado
        (date(2026, 9, 27), False),  # domingo
        (date(2026, 9, 7), False),  # feriado em segunda
        (date(2026, 2, 17), False),  # Carnaval
    ],
)
def test_dia_util(dia, esperado):
    assert dia_util(dia) is esperado


@pytest.mark.parametrize(
    ("pedido", "esperado"),
    [
        (date(2026, 9, 24), date(2026, 9, 24)),  # já é dia útil
        (date(2026, 9, 27), date(2026, 9, 25)),  # domingo volta para sexta
        (date(2026, 9, 7), date(2026, 9, 4)),  # feriado na segunda volta para sexta
        (date(2026, 2, 18), date(2026, 2, 18)),  # quarta de cinzas é dia útil
        (date(2026, 2, 17), date(2026, 2, 13)),  # Carnaval volta para a sexta anterior
        (date(2026, 4, 5), date(2026, 4, 2)),  # Páscoa: pula domingo, sábado e Sexta Santa
        (date(2027, 1, 1), date(2026, 12, 31)),  # atravessa a virada do ano
    ],
)
def test_ultimo_dia_util(pedido, esperado):
    assert ultimo_dia_util(pedido) == esperado


@given(anos)
def test_pascoa_e_sempre_domingo_entre_22_de_marco_e_25_de_abril(ano):
    p = pascoa(ano)
    assert p.weekday() == 6
    assert date(ano, 3, 22) <= p <= date(ano, 4, 25)


@given(anos)
def test_feriados_sao_todos_do_proprio_ano(ano):
    assert all(f.year == ano for f in feriados(ano))


@given(dias)
def test_ultimo_dia_util_e_o_mais_proximo_para_tras(dia):
    resultado = ultimo_dia_util(dia)
    assert resultado <= dia
    assert dia_util(resultado)
    # Nenhum dia útil entre o resultado e o dia pedido.
    entre = (resultado + timedelta(days=n) for n in range(1, (dia - resultado).days + 1))
    assert not any(dia_util(d) for d in entre)
