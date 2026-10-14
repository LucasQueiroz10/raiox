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
from app.core.identificadores import normalizar_isin, normalizar_ticker_b3
from app.core.traducao import AtivoIdentificado, TabelaIdentificacao

ARQUIVO = Path(__file__).with_name("exemplo.json")


def _isin(valor: str | None) -> str | None:
    return normalizar_isin(valor) if valor else None


class RepositorioExemplo:
    """Lê o arquivo uma vez e valida os identificadores; um arquivo inválido falha ao carregar."""

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
                    ativo_id=_isin(i["ativo_id"]),
                    peso=Decimal(i["peso"]),
                    tipo=TipoItem(i["tipo"]),
                    ativo_objeto=_isin(i.get("ativo_objeto")),
                    emissor=i.get("emissor"),
                )
                for i in c["itens"]
            )
            saida[fundo] = Composicao(
                fundo, date.fromisoformat(c["data_referencia"]), c["fonte"], itens
            )
        return saida

    @cached_property
    def _identificacao(self) -> TabelaIdentificacao:
        # Todos os ativos do exemplo são ISINs sintéticos: o ISIN é o próprio ativo_id.
        def ticker(valor: str | None) -> str | None:
            if valor and normalizar_ticker_b3(valor) != valor:
                raise ValueError("ticker fora do formato no conjunto de exemplo")
            return valor

        acoes = [
            AtivoIdentificado(
                normalizar_isin(a["ativo_id"]),
                TipoItem.ACAO,
                ticker_b3=ticker(a.get("ticker_b3")),
                isin=normalizar_isin(a["ativo_id"]),
            )
            for e in self._dados["empresas"]
            for a in e["ativos"]
        ]
        tickers_dos_fundos = self._dados["tickers_b3_dos_fundos"]
        fundos = [
            AtivoIdentificado(
                fundo, TipoItem.FUNDO, ticker_b3=ticker(tickers_dos_fundos.get(fundo)), isin=fundo
            )
            for fundo in self._composicoes
        ]
        return TabelaIdentificacao.montar(acoes + fundos)

    @cached_property
    def _empresa_do_ativo(self) -> dict[str, str]:
        ligacao: dict[str, str] = {}
        for e in self._dados["empresas"]:
            for a in e["ativos"]:
                ativo = normalizar_isin(a["ativo_id"])
                if ativo in ligacao:
                    raise ValueError("ativo ligado a mais de uma empresa no conjunto de exemplo")
                ligacao[ativo] = e["empresa_id"]
        return ligacao

    @cached_property
    def _tabela(self) -> TabelaClassificacao:
        classificacoes = {}
        for e in self._dados["empresas"]:
            c = e["classificacao"]
            if c is None:
                continue
            temas = tuple(
                ParticipacaoTema(t["tema"], t["subtema"], Decimal(t["peso"])) for t in c["temas"]
            )
            classificacoes[e["empresa_id"]] = Classificacao(
                e["empresa_id"], c["setor"], temas=temas, setor_origem=Origem(c["setor_origem"])
            )
        return TabelaClassificacao(self._dados["versao_classificacao"], classificacoes)

    @cached_property
    def _nomes(self) -> dict[str, str]:
        nomes = dict(self._dados["nomes"])
        for e in self._dados["empresas"]:
            nomes[e["empresa_id"]] = e["nome"]
            nomes.update({a["ativo_id"]: a["nome"] for a in e["ativos"] if "nome" in a})
        return nomes

    def aquecer(self) -> bool:
        """Os dados de exemplo já estão na memória: nada a reler."""
        return True

    def foto(self) -> RepositorioExemplo:
        """Os dados de exemplo não mudam: a foto é o próprio repositório."""
        return self

    def identificacao(self) -> TabelaIdentificacao:
        return self._identificacao

    def composicoes(self) -> Mapping[str, Composicao]:
        return self._composicoes

    def empresa_do_ativo(self) -> Mapping[str, str]:
        return self._empresa_do_ativo

    def tabela_classificacao(self) -> TabelaClassificacao:
        return self._tabela

    def nome(self, identificador: str) -> str | None:
        return self._nomes.get(identificador)
