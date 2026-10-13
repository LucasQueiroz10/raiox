"""Rotina comum a todas as cargas (ADR 0006, seção 5): CVM agora; PTAX, FCA e N-PORT depois.

O caminho de uma carga:

1. **Trava:** só uma carga de cada tipo por vez. Se o agendador repetir o job enquanto o anterior
   ainda roda, o segundo para logo, sem gravar nada (`trava`).
2. **Carga parada:** uma carga que ficou em "carregando" além do tempo limite (o processo caiu no
   meio) vira "com_erro" antes de a próxima começar (`expirar_paradas`).
3. **Abertura:** a carga nasce "carregando", numa transação própria, e fica visível mesmo se o
   processo cair depois (`publicar_carga`).
4. **Gravação e publicação numa transação só:** a função de gravação de cada fonte prepara os dados
   (tabelas temporárias da sessão), valida e insere nas tabelas definitivas; a carga passa a
   "publicada" na mesma transação. A API só enxerga a carga publicada (visões *_vigente).
5. **Erro:** qualquer exceção desfaz a transação inteira (nada fica gravado) e a carga fica
   "com_erro", com o motivo. A exceção segue para cima: o job termina com erro e o alerta dispara
   (ADR 0007, seção 8).

As regras do próprio banco reforçam o caminho: linha só entra em carga "carregando" do tipo certo,
e carga publicada ou com erro não muda mais (migração 0002).

A conexão precisa estar em autocommit: cada passo controla a própria transação.
"""

import zlib
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date, timedelta

import psycopg

# Uma carga da CVM leva minutos; três horas em "carregando" só acontece se o processo caiu.
TEMPO_LIMITE = timedelta(hours=3)
# O motivo do erro vai para o banco e para o log: curto, e nunca com o conteúdo das linhas.
TAMANHO_DO_MOTIVO = 500

# Recebe a conexão (já dentro da transação) e o carga_id; devolve quantas linhas gravou.
type Gravar = Callable[[psycopg.Connection, int], int]


class ErroDeValidacao(Exception):
    """A validação recusou os dados. A mensagem vira o motivo do erro: diz o que falhou, nunca o
    dado que falhou (ele pode ser, por exemplo, um CPF que escapou)."""


class CargaEmAndamento(Exception):
    """Outra carga do mesmo tipo está rodando."""


@contextmanager
def trava(conexao: psycopg.Connection, tipo: str) -> Iterator[None]:
    """Segura a trava do tipo de carga até o fim do bloco; levanta CargaEmAndamento se outra
    sessão já a tem.

    Usa a trava consultiva do PostgreSQL (advisory lock) da sessão: some sozinha se a conexão cair,
    então um job que morreu no meio não deixa a trava presa.
    """
    chave = zlib.crc32(f"rx:carga:{tipo}".encode())
    (conseguiu,) = conexao.execute("SELECT pg_try_advisory_lock(%s)", (chave,)).fetchone()
    if not conseguiu:
        raise CargaEmAndamento(f"outra carga do tipo {tipo} está rodando")
    try:
        yield
    finally:
        conexao.execute("SELECT pg_advisory_unlock(%s)", (chave,))


def expirar_paradas(conexao: psycopg.Connection, tipo: str) -> int:
    """Marca como "com_erro" as cargas do tipo paradas em "carregando" além do TEMPO_LIMITE e
    devolve quantas eram. Chamar com a trava do tipo, para não pegar uma carga que ainda roda."""
    cursor = conexao.execute(
        "UPDATE ref.carga SET status = 'com_erro',"
        " motivo_erro = 'parada em carregando além do tempo limite'"
        " WHERE tipo = %s AND status = 'carregando'"
        " AND iniciada_em < clock_timestamp() - %s",
        (tipo, TEMPO_LIMITE),
    )
    return cursor.rowcount


def _abrir(conexao: psycopg.Connection, tipo: str, fonte: str, data_referencia: date | None) -> int:
    """Registra a carga "carregando" (fica gravada já: a conexão está em autocommit)."""
    (carga_id,) = conexao.execute(
        "INSERT INTO ref.carga (tipo, fonte, data_referencia) VALUES (%s, %s, %s)"
        " RETURNING carga_id",
        (tipo, fonte, data_referencia),
    ).fetchone()
    return carga_id


def _motivo(erro: BaseException) -> str:
    return f"{type(erro).__name__}: {erro}"[:TAMANHO_DO_MOTIVO]


def _marcar_erro(conexao: psycopg.Connection, carga_id: int, erro: BaseException) -> None:
    conexao.execute(
        "UPDATE ref.carga SET status = 'com_erro', motivo_erro = %s WHERE carga_id = %s",
        (_motivo(erro), carga_id),
    )


def publicar_carga(
    conexao: psycopg.Connection,
    tipo: str,
    fonte: str,
    data_referencia: date | None,
    gravar: Gravar,
) -> int:
    """Abre a carga, grava e publica numa transação só e devolve o carga_id.

    Em qualquer erro de `gravar` (validação, banco, programa), a transação é desfeita, a carga
    fica "com_erro" com o motivo e a exceção é levantada de novo.
    """
    carga_id = _abrir(conexao, tipo, fonte, data_referencia)
    try:
        with conexao.transaction():
            linhas = gravar(conexao, carga_id)
            conexao.execute(
                "UPDATE ref.carga SET status = 'publicada', linhas = %s WHERE carga_id = %s",
                (linhas, carga_id),
            )
    except BaseException as erro:
        _marcar_erro(conexao, carga_id, erro)
        raise
    return carga_id


def registrar_falha(
    conexao: psycopg.Connection,
    tipo: str,
    fonte: str,
    data_referencia: date | None,
    erro: BaseException,
) -> int:
    """Registra uma carga que falhou antes de haver o que gravar (ex.: o download caiu ou o
    arquivo mudou de formato): abre e já marca "com_erro", para o histórico e o alerta."""
    carga_id = _abrir(conexao, tipo, fonte, data_referencia)
    _marcar_erro(conexao, carga_id, erro)
    return carga_id
