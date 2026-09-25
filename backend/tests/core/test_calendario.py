from datetime import date

import pytest

from app.core.calendario import feriados, pascoa


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
