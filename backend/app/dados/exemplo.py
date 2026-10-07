"""Repositório com o conjunto de exemplo sintético (app/dados/exemplo.json)."""

import json
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from functools import cached_property
from pathlib import Path

from app.core.classificacao import (
    Classificacao,
    Origem,
    ParticipacaoTema,
    TabelaClassificacao,
)
from app.core.composicao import Composicao, ItemComposicao, TipoItem
from app.core.identificadores import normalizar_isin

ARQUIVO = Path(__file__).with_name("exemplo.json")


def _isin(valor: str | None) -> str | None:
    return normalizar_isin(valor) if valor else None


class RepositorioExemplo:
    """Lê o arquivo uma vez e valida os ISINs; um arquivo inválido falha ao carregar."""

    def __init__(self, arquivo: Path = ARQUIVO) -> None:
        self._arquivo = arquivo

    @cached_property
    def _dados(self) -> dict:
        return json.loads(self._arquivo.read_text(encoding="utf-8"))

    @cached_property
    def _composicoes(self) -> dict[str, Composicao]:
        saida = {}
        for c in self._dados["composicoes"]:
            fundo = normalizar_isin(c["fundo"])
            itens = tuple(
                ItemComposicao(
                    ativo_id=_isin(i["isin"]),
                    peso=Decimal(i["peso"]),
                    tipo=TipoItem(i["tipo"]),
                    ativo_objeto=_isin(i.get("ativo_objeto_isin")),
                    emissor=_isin(i.get("emissor_isin")),
                )
                for i in c["itens"]
            )
            saida[fundo] = Composicao(
                fundo, date.fromisoformat(c["data_referencia"]), c["fonte"], itens
            )
        return saida

    @cached_property
    def _tabela(self) -> TabelaClassificacao:
        classificacoes = {}
        for c in self._dados["classificacoes"]:
            isin = normalizar_isin(c["isin"])
            temas = tuple(
                ParticipacaoTema(t["tema"], t["subtema"], Decimal(t["peso"])) for t in c["temas"]
            )
            classificacoes[isin] = Classificacao(
                isin, c["setor"], temas=temas, setor_origem=Origem(c["setor_origem"])
            )
        return TabelaClassificacao(self._dados["versao_classificacao"], classificacoes)

    def composicoes(self) -> Mapping[str, Composicao]:
        return self._composicoes

    def tabela_classificacao(self) -> TabelaClassificacao:
        return self._tabela

    def nome(self, identificador: str) -> str | None:
        return self._dados["nomes"].get(identificador)
