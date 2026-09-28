import pytest

from app.api.raiox import obter_limitador_raiox, obter_limite_de_analises


@pytest.fixture(autouse=True)
def limites_zerados():
    """Os limites de requisição são globais do servidor; cada teste começa com a conta zerada."""
    obter_limitador_raiox.cache_clear()
    obter_limite_de_analises.cache_clear()
