import pytest

from app.config import Config


def test_padrao_e_desenvolvimento_liberando_o_front_local():
    c = Config.do_ambiente({})

    assert c.producao is False
    assert c.origens_permitidas == ("http://localhost:5173",)


def test_producao_sem_origens_configuradas_nao_libera_nenhuma():
    c = Config.do_ambiente({"RX_AMBIENTE": "producao"})

    assert c.producao is True
    assert c.origens_permitidas == ()


def test_origens_separadas_por_virgula():
    c = Config.do_ambiente(
        {
            "RX_AMBIENTE": "producao",
            "RX_ORIGENS_PERMITIDAS": "https://rx.exemplo, https://www.rx.exemplo",
        }
    )

    assert c.origens_permitidas == ("https://rx.exemplo", "https://www.rx.exemplo")


@pytest.mark.parametrize(
    "ambiente",
    [
        {"RX_AMBIENTE": "prod"},  # erro de digitação não pode virar desenvolvimento em silêncio
        {"RX_ORIGENS_PERMITIDAS": "*"},  # curinga abriria o CORS para qualquer site
        {"RX_ORIGENS_PERMITIDAS": "rx.exemplo"},  # origem sem esquema
    ],
)
def test_configuracao_invalida_falha_na_partida(ambiente):
    with pytest.raises(ValueError):
        Config.do_ambiente(ambiente)
