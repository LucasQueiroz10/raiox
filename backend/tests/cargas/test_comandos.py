"""Os comandos das cargas com o banco fora do ar: terminam com 1 e mensagem curta, sem traceback
(revisão do PR #70). Sem banco nem rede: a porta 1 do próprio computador não tem banco. O tempo
limite curto evita os 130 s de espera padrão do psycopg no Windows, que não percebe a recusa.
"""

import re

import pytest

from cargas import cadastro, cvm

FORA_DO_AR = "postgresql+psycopg://rx_ingestao@127.0.0.1:1/rx?connect_timeout=2"


@pytest.mark.parametrize("comando", [cvm.main, cadastro.main], ids=["cvm", "cadastro"])
def test_banco_fora_do_ar_termina_com_1_sem_traceback(comando, monkeypatch, caplog, capsys):
    monkeypatch.setenv("RX_BANCO_URL", FORA_DO_AR)

    assert comando([]) == 1

    # Só o nome da classe (no Windows, a porta fechada vira ConnectionTimeout, subclasse).
    (erro,) = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    assert re.fullmatch(r".* \((OperationalError|ConnectionTimeout)\)", erro)
    assert "127.0.0.1" not in caplog.text  # nem o endereço do banco
    assert all(r.exc_info is None for r in caplog.records)
    assert "Traceback" not in capsys.readouterr().err
