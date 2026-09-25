from datetime import date

import pytest

from app.core.calendario import pascoa


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
