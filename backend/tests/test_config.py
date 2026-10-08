import pytest

from app.config import Config

BANCO = "postgresql+psycopg://rx_api@127.0.0.1:5433/rx"


def test_padrao_e_desenvolvimento_liberando_o_front_local():
    c = Config.do_ambiente({})

    assert c.producao is False
    assert c.origens_permitidas == ("http://localhost:5173",)


def test_producao_sem_origens_configuradas_nao_libera_nenhuma():
    c = Config.do_ambiente({"RX_AMBIENTE": "producao", "RX_BANCO_URL": BANCO})

    assert c.producao is True
    assert c.origens_permitidas == ()


def test_origens_separadas_por_virgula():
    c = Config.do_ambiente(
        {
            "RX_AMBIENTE": "producao",
            "RX_BANCO_URL": BANCO,
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
        {"RX_AMBIENTE": "producao"},  # produção nunca roda com os dados de exemplo
        {"RX_BANCO_URL": "postgresql://rx_api@127.0.0.1:5433/rx"},  # sem o driver psycopg
        {"RX_BANCO_URL": "sqlite:///rx.db"},
    ],
)
def test_configuracao_invalida_falha_na_partida(ambiente):
    with pytest.raises(ValueError):
        Config.do_ambiente(ambiente)


def test_desenvolvimento_sem_banco_usa_o_exemplo():
    assert Config.do_ambiente({}).banco_url is None


def test_le_a_url_do_banco():
    assert Config.do_ambiente({"RX_BANCO_URL": BANCO}).banco_url == BANCO


def test_url_do_banco_fica_fora_do_repr_e_das_mensagens_de_erro():
    # A URL de produção leva a senha: não pode aparecer em log nem em mensagem de erro.
    c = Config.do_ambiente({"RX_BANCO_URL": BANCO})
    assert "rx_api@" not in repr(c)

    with pytest.raises(ValueError) as erro:
        Config.do_ambiente({"RX_BANCO_URL": "postgresql://rx_api@servidor-sintetico/rx"})
    assert "servidor-sintetico" not in str(erro.value)


def test_url_do_banco_malformada_falha_na_partida_sem_repetir_pedacos_dela():
    # Uma senha com caractere especial sem escape cai na porta ou no servidor, e a mensagem do
    # SQLAlchemy repetiria esse pedaço.
    with pytest.raises(ValueError) as erro:
        Config.do_ambiente(
            {"RX_BANCO_URL": "postgresql+psycopg://rx_api@servidor-sintetico:porta/rx"}
        )

    assert "porta" not in str(erro.value)
    assert "servidor-sintetico" not in str(erro.value)
    assert erro.value.__suppress_context__  # o erro original não aparece no traceback
