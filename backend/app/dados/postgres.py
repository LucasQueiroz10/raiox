"""Repositório dos dados públicos no PostgreSQL (ADR 0006).

Lê só as visões dos dados vigentes (o usuário da API, rx_api, não enxerga mais nada), numa
transação só de leitura e REPEATABLE READ: todas as consultas veem o mesmo momento do banco.

Guarda uma foto dos dados em memória e só relê quando sai uma carga nova, conferindo no máximo a
cada INTERVALO_S segundos. Se o banco cair ou trouxer um dado inválido depois da primeira leitura,
segue com a última foto. DT-10 (docs/divida_tecnica.md): a foto tem todas as composições vigentes.
"""

import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import replace

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.classificacao import (
    Classificacao,
    Origem,
    ParticipacaoTema,
    Status,
    TabelaClassificacao,
)
from app.core.composicao import Composicao, ItemComposicao, TipoItem

INTERVALO_S = 60  # de quanto em quanto tempo, no máximo, confere se saiu carga nova
SEM_CLASSIFICACAO = "nenhuma"  # versão da tabela enquanto nenhuma classificação foi publicada

log = logging.getLogger(__name__)


class DadosIndisponiveis(Exception):
    """O banco não respondeu e ainda não há dados lidos."""


class FotoDados:
    """Os dados vigentes num momento do banco. Implementa o RepositorioDados."""

    def __init__(
        self,
        composicoes: Mapping[str, Composicao],
        empresa_do_ativo: Mapping[str, str],
        tabela: TabelaClassificacao,
        nomes: Mapping[str, str],
    ) -> None:
        self._composicoes = composicoes
        self._empresa_do_ativo = empresa_do_ativo
        self._tabela = tabela
        self._nomes = nomes

    def composicoes(self) -> Mapping[str, Composicao]:
        return self._composicoes

    def empresa_do_ativo(self) -> Mapping[str, str]:
        return self._empresa_do_ativo

    def tabela_classificacao(self) -> TabelaClassificacao:
        return self._tabela

    def nome(self, identificador: str) -> str | None:
        return self._nomes.get(identificador)


def versao_dos_dados(conexao: Connection) -> tuple:
    """Muda a cada carga publicada que entra na foto. A PTAX fica de fora: sai todo dia e não
    muda nada da foto."""
    linha = conexao.execute(
        text("SELECT count(*), max(publicada_em) FROM ref.carga_publicada WHERE tipo <> 'ptax'")
    ).one()
    return tuple(linha)


def ler_foto(conexao: Connection) -> FotoDados:
    # Identificador antigo ou de menor prioridade -> empresa_id atual (ADR 0005, seção 3).
    apelidos: dict[str, str] = dict(
        conexao.execute(text("SELECT apelido, empresa_id FROM ref.empresa_apelido_vigente")).all()
    )

    def atual(empresa_id: str | None) -> str | None:
        return apelidos.get(empresa_id, empresa_id) if empresa_id else None

    nomes: dict[str, str] = {}

    itens: dict[int, list[ItemComposicao]] = defaultdict(list)
    for r in conexao.execute(
        text(
            "SELECT composicao_id, ativo_id, empresa_id, tipo, peso, ativo_objeto, emissor"
            " FROM ref.composicao_item_vigente ORDER BY composicao_id, ordem"
        )
    ):
        itens[r.composicao_id].append(
            ItemComposicao(
                ativo_id=r.ativo_id,
                peso=r.peso,
                tipo=TipoItem(r.tipo),
                ativo_objeto=r.ativo_objeto,
                emissor=atual(r.emissor),
                empresa_id=atual(r.empresa_id),
            )
        )

    composicoes: dict[str, Composicao] = {}
    for r in conexao.execute(
        text(
            "SELECT composicao_id, fundo_id, nome_fundo, data_referencia, fonte"
            " FROM ref.composicao_vigente"
        )
    ):
        composicoes[r.fundo_id] = Composicao(
            r.fundo_id, r.data_referencia, r.fonte, tuple(itens[r.composicao_id])
        )
        if r.nome_fundo:
            nomes[r.fundo_id] = r.nome_fundo  # sem nome na identificação, vale o da fonte

    proprias = dict(composicoes)
    empresa_do_ativo: dict[str, str] = {}
    for r in conexao.execute(
        text("SELECT ativo_id, empresa_id, nome, aproximado_por FROM ref.ativo_vigente")
    ):
        if r.empresa_id:
            empresa_do_ativo[r.ativo_id] = r.empresa_id
        if r.nome:
            nomes[r.ativo_id] = r.nome
        # UCITS sem composição própria: usa a do ETF americano do mesmo índice, com o rótulo.
        if r.aproximado_por in proprias and r.ativo_id not in proprias:
            composicoes[r.ativo_id] = replace(
                proprias[r.aproximado_por], fundo_id=r.ativo_id, aproximado_por=r.aproximado_por
            )

    for r in conexao.execute(text("SELECT empresa_id, nome FROM ref.empresa_vigente")):
        nomes[r.empresa_id] = r.nome

    return FotoDados(composicoes, empresa_do_ativo, _ler_tabela(conexao, atual), nomes)


def _ler_tabela(
    conexao: Connection, atual: Callable[[str | None], str | None]
) -> TabelaClassificacao:
    temas: dict[str, list[ParticipacaoTema]] = defaultdict(list)
    for r in conexao.execute(
        text(
            "SELECT empresa_id, tema, subtema, peso, origem, status"
            " FROM ref.classificacao_tema_vigente ORDER BY empresa_id, tema, subtema"
        )
    ):
        temas[r.empresa_id].append(
            ParticipacaoTema(
                r.tema, r.subtema, r.peso, origem=Origem(r.origem), status=Status(r.status)
            )
        )

    linhas = conexao.execute(
        text("SELECT empresa_id, setor, setor_origem, setor_status FROM ref.classificacao_vigente")
    ).all()
    classificacoes: dict[str, Classificacao] = {}
    # Primeiro as linhas já com o empresa_id atual; a de um apelido só vale se a empresa atual
    # não tiver a sua (classificação publicada antes da troca de identificador).
    for r in sorted(linhas, key=lambda r: atual(r.empresa_id) != r.empresa_id):
        empresa_id = atual(r.empresa_id)
        if empresa_id not in classificacoes:
            classificacoes[empresa_id] = Classificacao(
                empresa_id,
                r.setor,
                temas=tuple(temas[r.empresa_id]),
                setor_origem=Origem(r.setor_origem),
                setor_status=Status(r.setor_status),
            )

    versao = conexao.execute(
        text(
            "SELECT carga_id, publicada_em FROM ref.carga_publicada WHERE tipo = 'classificacao'"
            " ORDER BY publicada_em DESC, carga_id DESC LIMIT 1"
        )
    ).one_or_none()
    rotulo = f"{versao.publicada_em:%Y-%m-%d}.{versao.carga_id}" if versao else SEM_CLASSIFICACAO
    return TabelaClassificacao(rotulo, classificacoes)


class RepositorioPostgres:
    """Implementa o RepositorioDados com a foto vigente (ver o início do módulo).

    Quem precisa de várias leituras coerentes entre si (uma análise inteira) usa foto() uma vez.
    """

    def __init__(
        self,
        motor: Engine,
        *,
        intervalo_s: float = INTERVALO_S,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._motor = motor
        self._intervalo_s = intervalo_s
        self._relogio = relogio
        self._trava = threading.Lock()
        self._foto: FotoDados | None = None
        self._versao: tuple | None = None
        self._proxima_conferencia = 0.0

    def foto(self) -> FotoDados:
        with self._trava:
            if self._foto is not None and self._relogio() < self._proxima_conferencia:
                return self._foto
            try:
                self._atualizar()
            except (SQLAlchemyError, ValueError) as erro:
                # Só o tipo do erro: a mensagem do driver pode trazer o endereço do banco.
                if self._foto is None:
                    log.warning("Dados públicos indisponíveis (%s).", type(erro).__name__)
                    raise DadosIndisponiveis("dados públicos indisponíveis") from erro
                log.warning(
                    "Falha ao reler os dados (%s); segue com a última foto.", type(erro).__name__
                )
            self._proxima_conferencia = self._relogio() + self._intervalo_s
            return self._foto

    def _atualizar(self) -> None:
        with self._motor.connect() as conexao:
            conexao.execution_options(isolation_level="REPEATABLE READ", postgresql_readonly=True)
            versao = versao_dos_dados(conexao)
            if self._foto is None or versao != self._versao:
                self._foto = ler_foto(conexao)
                self._versao = versao

    def fechar(self) -> None:
        """Fecha as conexões abertas com o banco (ao desligar o servidor)."""
        self._motor.dispose()

    def composicoes(self) -> Mapping[str, Composicao]:
        return self.foto().composicoes()

    def empresa_do_ativo(self) -> Mapping[str, str]:
        return self.foto().empresa_do_ativo()

    def tabela_classificacao(self) -> TabelaClassificacao:
        return self.foto().tabela_classificacao()

    def nome(self, identificador: str) -> str | None:
        return self.foto().nome(identificador)
