"""Mede o pior caso da análise (DT-4) com carteiras sintéticas grandes, pelo caminho inteiro da API:
validação da entrada, abertura dos fundos, agregação e a resposta em JSON.

Só dados sintéticos (prefixo ZZ). Os pesos têm 50 dígitos, como os que a carga calcula (ADR 0006).
Não roda no CI. Uso, dentro de backend/:
    python -m medicoes.pior_caso
"""

import statistics
import threading
import time
import tracemalloc
from datetime import date
from decimal import Decimal, localcontext

from fastapi.testclient import TestClient

from app.api.raiox import obter_limitador_raiox
from app.api.seguranca import LimitadorPorJanela
from app.config import Config
from app.core.agregacao import agregar
from app.core.classificacao import (
    Classificacao,
    Origem,
    ParticipacaoTema,
    TabelaClassificacao,
)
from app.core.composicao import Composicao, ItemComposicao, Posicao, TipoItem
from app.core.identificadores import digito_verificador
from app.core.lookthrough import MAX_PASSOS, PRECISAO, abrir_carteira
from app.dados.postgres import FotoDados
from app.main import criar_app

SETORES = ("Tecnologia", "Financeiro", "Energia", "Saúde", "Indústria", "Consumo", "Materiais")
REPETICOES = 3


def _isin(prefixo: str, n: int) -> str:
    corpo = f"ZZ{prefixo}{n:0{9 - len(prefixo)}d}"
    return corpo + digito_verificador(corpo)


def acao(n: int) -> str:
    return _isin("A", n)


def fundo(n: int) -> str:
    return _isin("F", n)


def _composicao(fundo_id: str, ativos: list[str], tipo: TipoItem) -> Composicao:
    with localcontext(prec=PRECISAO):
        peso = Decimal("0.99") / len(ativos)  # 50 dígitos; 1% fica em caixa
    itens = [ItemComposicao(a, peso, tipo) for a in ativos]
    itens.append(ItemComposicao(None, Decimal("0.01"), TipoItem.CAIXA))
    return Composicao(fundo_id, date(2026, 8, 31), "fonte sintética", tuple(itens))


class Universo:
    """Empresas sintéticas, cada uma com uma ação, e os fundos que as contêm."""

    def __init__(self, empresas: int) -> None:
        self.composicoes: dict[str, Composicao] = {}
        self.empresa_do_ativo = {acao(n): f"ZZ:E{n}" for n in range(empresas)}
        classificacoes = {}
        for n in range(empresas):
            empresa = f"ZZ:E{n}"
            temas = ()
            if n % 10 < 3:  # 30% das empresas com um tema aprovado
                temas = (
                    ParticipacaoTema(
                        "Cadeia de IA", f"Subtema {n % 5}", Decimal("0.2"), origem=Origem.MANUAL
                    ),
                )
            classificacoes[empresa] = Classificacao(empresa, SETORES[n % len(SETORES)], temas)
        self.tabela = TabelaClassificacao("medicao", classificacoes)
        self.proximo_fundo = 0

    def etf(self, inicio: int, tamanho: int) -> str:
        """ETF com as ações [inicio, inicio + tamanho) do universo."""
        fundo_id = fundo(self.proximo_fundo)
        self.proximo_fundo += 1
        ativos = [acao(n) for n in range(inicio, inicio + tamanho)]
        self.composicoes[fundo_id] = _composicao(fundo_id, ativos, TipoItem.ACAO)
        return fundo_id

    def fundo_de_fundos(self, fundos: list[str]) -> str:
        fundo_id = fundo(self.proximo_fundo)
        self.proximo_fundo += 1
        self.composicoes[fundo_id] = _composicao(fundo_id, fundos, TipoItem.FUNDO)
        return fundo_id

    def dados(self) -> FotoDados:
        return FotoDados(self.composicoes, self.empresa_do_ativo, self.tabela, {})


class Fonte:
    def __init__(self, foto: FotoDados) -> None:
        self._foto = foto

    def foto(self) -> FotoDados:
        return self._foto


def _corpo(fundos: list[str], acoes: list[str]) -> dict:
    posicoes = [{"isin": f, "valor": "1000.00", "moeda": "BRL", "tipo": "fundo"} for f in fundos]
    posicoes += [{"isin": a, "valor": "100.00", "moeda": "BRL", "tipo": "acao"} for a in acoes]
    return {"posicoes": posicoes}


def _cliente(dados: FotoDados) -> TestClient:
    app = criar_app(Config(producao=False, origens_permitidas=()))
    app.state.dados = Fonte(dados)
    # A medição faz muitas análises seguidas do mesmo IP: sem o limite por minuto.
    app.dependency_overrides[obter_limitador_raiox] = lambda: LimitadorPorJanela(10**9, 60)
    return TestClient(app)


def medir(nome: str, universo: Universo, fundos: list[str], acoes: list[str]) -> float:
    dados = universo.dados()
    corpo = _corpo(fundos, acoes)
    cliente = _cliente(dados)

    tempos, resposta = [], None
    for _ in range(REPETICOES):
        inicio = time.perf_counter()
        resposta = cliente.post("/raiox", json=corpo)
        tempos.append(time.perf_counter() - inicio)
        if resposta.status_code != 200:
            raise RuntimeError(f"a análise respondeu {resposta.status_code}")
    api = statistics.median(tempos)

    posicoes = [Posicao(f, Decimal("1000.00"), TipoItem.FUNDO) for f in fundos]
    posicoes += [Posicao(a, Decimal("100.00"), TipoItem.ACAO) for a in acoes]
    inicio = time.perf_counter()
    resultado = abrir_carteira(
        posicoes, dados.composicoes(), empresa_do_ativo=dados.empresa_do_ativo()
    )
    meio = time.perf_counter()
    agregar(resultado, dados.tabela_classificacao())
    fim = time.perf_counter()

    tracemalloc.start()
    cliente.post("/raiox", json=corpo)
    pico_mb = tracemalloc.get_traced_memory()[1] / 2**20
    tracemalloc.stop()

    avisos = sorted({a["codigo"] for a in resposta.json()["avisos"]}) or ["-"]
    print(
        f"{nome:<44} {len(fundos):>4} {len(acoes):>4} {len(resultado.empresas):>8,}"
        f" {api:>7.2f} {meio - inicio:>7.2f} {fim - meio:>7.2f} {pico_mb:>7.0f}"
        f" {len(resposta.content) / 1024:>6.0f}  {','.join(avisos)}"
    )
    return api


def medir_simultaneas(universo: Universo, fundos: list[str], acoes: list[str], vezes: int) -> None:
    """Várias análises ao mesmo tempo: o cálculo usa CPU e o Python roda uma thread por vez."""
    cliente = _cliente(universo.dados())
    corpo = _corpo(fundos, acoes)
    tempos: list[float] = []
    codigos: list[int] = []

    def uma() -> None:
        inicio = time.perf_counter()
        codigos.append(cliente.post("/raiox", json=corpo).status_code)
        tempos.append(time.perf_counter() - inicio)

    threads = [threading.Thread(target=uma) for _ in range(vezes)]
    inicio = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(
        f"{vezes} análises simultâneas: todas terminam em {time.perf_counter() - inicio:.2f} s;"
        f" a mais rápida {min(tempos):.2f} s, a mais lenta {max(tempos):.2f} s;"
        f" códigos {sorted(codigos)}"
    )


def comparar_trava(
    universo: Universo, trava: int, globais: list[str], fofs: list[str], acoes: list[str]
) -> None:
    """Quanto a abertura dos fundos levaria com outra trava de passos (só o motor)."""
    resultados = []
    for fundos in (globais, fofs):
        posicoes = [Posicao(f, Decimal("1000.00"), TipoItem.FUNDO) for f in fundos]
        posicoes += [Posicao(a, Decimal("100.00"), TipoItem.ACAO) for a in acoes]
        inicio = time.perf_counter()
        r = abrir_carteira(
            posicoes,
            universo.composicoes,
            empresa_do_ativo=universo.empresa_do_ativo,
            max_passos=trava,
        )
        cortou = "corta" if r.avisos else "inteira"
        resultados.append(f"{time.perf_counter() - inicio:.2f} s ({cortou})")
    print(
        f"trava de {trava:>9,} passos: 100 ETFs globais {resultados[0]}; 100 FoFs {resultados[1]}"
    )


def main() -> None:
    print(
        f"{'cenário':<44} {'fund':>4} {'ações':>4} {'empresas':>8} {'API s':>7}"
        f" {'abrir s':>7} {'agreg s':>7} {'pico MB':>7} {'KB':>6}  avisos"
    )

    u = Universo(9_000)
    etfs = [u.etf(0, 500) for _ in range(10)]
    medir("típica: 10 ETFs de 500 + 20 ações", u, etfs, [acao(n) for n in range(20)])

    u = Universo(9_000)
    etfs = [u.etf(0, 3_000) for _ in range(20)] + [u.etf(0, 9_000) for _ in range(10)]
    medir("pesada: 20 ETFs de 3.000 + 10 de 9.000", u, etfs, [acao(n) for n in range(100)])

    u = Universo(9_000)
    globais = [u.etf(0, 9_000) for _ in range(100)]
    acoes = [acao(n) for n in range(400)]
    medir("limite: 100 ETFs globais (mesmas 9.000)", u, globais, acoes)

    # As composições vêm dos nossos dados, não do usuário: as empresas distintas ficam limitadas ao
    # universo dos dados (dezenas de milhares), não a 100 x 9.000.
    u = Universo(30_000)
    misturados = [u.etf((n * 210) % 21_000, 9_000) for n in range(100)]
    medir("limite: 100 ETFs num universo de 30.000", u, misturados, acoes)

    u = Universo(9_000)
    base = [u.etf(0, 9_000) for _ in range(10)]
    fofs = [u.fundo_de_fundos(base) for _ in range(100)]
    medir("trava: 100 fundos de fundos de 10 globais", u, fofs, acoes)

    print()
    u = Universo(9_000)
    globais = [u.etf(0, 9_000) for _ in range(100)]
    base = [u.etf(0, 9_000) for _ in range(10)]
    fofs = [u.fundo_de_fundos(base) for _ in range(100)]
    for trava in sorted({1_000_000, 500_000, MAX_PASSOS}, reverse=True):
        comparar_trava(u, trava, globais, fofs, acoes)

    print()
    medir_simultaneas(u, globais, acoes, vezes=4)


if __name__ == "__main__":
    main()
