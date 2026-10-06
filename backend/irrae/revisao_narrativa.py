"""Revisão manual do componente N (D-11): amostra de frases rotuladas e precisão do rótulo.

1. `amostra`: lê os 10-K em HTML de uma pasta (um arquivo por empresa, `<empresa>.html`), rotula
   cada frase do N com a folha (ou "nenhuma") e sorteia ~200, estratificadas por rótulo e por
   empresa. Grava um CSV com a coluna `rotulo_manual` vazia para o M1 preencher.
2. `precisao`: depois da rotulagem, compara o rótulo automático com o manual.

O CSV tem frases de 10-Ks reais: fica na pasta compartilhada, nunca no repositório (só dados
sintéticos no repositório). Os HTML são baixados fora do repositório.

Uso (de dentro de backend/):
    python -m irrae.revisao_narrativa amostra --html <pasta> --saida <arquivo.csv> [--n 200]
    python -m irrae.revisao_narrativa precisao --csv <arquivo.csv>
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from ingest.narrativa import folhas_da_frase, frases_narrativa

REPOSITORIO = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).resolve().parent / "config"
COLUNAS = ["frase", "empresa", "item", "rotulo_automatico", "rotulo_manual"]
NENHUMA = "nenhuma"


def rotular(
    html: str | bytes, dicionario: dict[str, list[str]], filtro: dict, empresa: str
) -> list[dict]:
    """Cada frase que entra no N, com o item de origem e as folhas citadas (ou "nenhuma")."""
    linhas = []
    for item, frase in frases_narrativa(html, filtro):
        folhas = sorted(folhas_da_frase(frase, dicionario))
        rotulo = ";".join(folhas) if folhas else NENHUMA
        linhas.append(
            {"frase": frase, "empresa": empresa, "item": item, "rotulo_automatico": rotulo}
        )
    return linhas


def amostra_estratificada(linhas: list[dict], n: int, semente: int) -> list[dict]:
    """Sorteia n frases, divididas igualmente entre os rótulos (incluindo "nenhuma").

    Rótulo com menos frases que a sua parte entra inteiro, e a sobra vai para os outros. Dentro
    de cada rótulo, as empresas se alternam, para nenhuma dominar a amostra."""
    rng = np.random.default_rng(semente)
    por_rotulo: dict[str, dict[str, list[dict]]] = {}
    for linha in linhas:
        empresas = por_rotulo.setdefault(linha["rotulo_automatico"], {})
        empresas.setdefault(linha["empresa"], []).append(linha)
    filas = {}
    for rotulo in sorted(por_rotulo):
        empresas = por_rotulo[rotulo]
        ordem = sorted(empresas)
        rng.shuffle(ordem)
        for e in ordem:
            rng.shuffle(empresas[e])
        filas[rotulo] = _alternar([empresas[e] for e in ordem])

    cotas = dict.fromkeys(filas, 0)
    restante = min(n, len(linhas))
    while restante:
        abertos = [r for r in sorted(filas) if cotas[r] < len(filas[r])]
        parte, sobra = divmod(restante, len(abertos))
        rng.shuffle(abertos)
        for i, r in enumerate(abertos):
            quer = parte + (1 if i < sobra else 0)
            dado = min(quer, len(filas[r]) - cotas[r])
            cotas[r] += dado
            restante -= dado
    return [linha for r in sorted(filas) for linha in filas[r][: cotas[r]]]


def _alternar(listas: list[list[dict]]) -> list[dict]:
    saida = []
    for i in range(max((len(x) for x in listas), default=0)):
        saida.extend(x[i] for x in listas if i < len(x))
    return saida


def exigir_fora_do_repositorio(caminho: Path) -> None:
    alvo = Path(caminho).resolve()
    if alvo == REPOSITORIO or REPOSITORIO in alvo.parents:
        raise ValueError(
            "a amostra tem frases de 10-Ks reais: grave fora do repositório (pasta compartilhada)"
        )


def escrever_csv(linhas: list[dict], caminho: Path) -> None:
    with Path(caminho).open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({**{c: linha.get(c, "") for c in COLUNAS}, "rotulo_manual": ""})


def ler_csv(caminho: Path) -> list[dict]:
    with Path(caminho).open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def precisao(linhas: list[dict]) -> dict:
    """Fração das frases já rotuladas à mão em que o rótulo automático acertou, no total e por
    rótulo automático. Compara o conjunto de folhas (a ordem e os espaços não importam)."""

    def folhas(rotulo: str) -> frozenset[str]:
        return frozenset(f.strip() for f in rotulo.split(";") if f.strip())

    def resumo(grupo: list[dict]) -> dict:
        acertos = sum(folhas(r["rotulo_automatico"]) == folhas(r["rotulo_manual"]) for r in grupo)
        return {
            "rotuladas": len(grupo),
            "acertos": acertos,
            "precisao": acertos / len(grupo) if grupo else 0.0,
        }

    rotuladas = [r for r in linhas if r.get("rotulo_manual", "").strip()]
    por_rotulo: dict[str, list[dict]] = {}
    for r in rotuladas:
        por_rotulo.setdefault(r["rotulo_automatico"], []).append(r)
    return {
        **resumo(rotuladas),
        "por_rotulo": {k: resumo(v) for k, v in sorted(por_rotulo.items())},
    }


def _config(nome: str) -> dict:
    return json.loads((CONFIG / nome).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="comando", required=True)
    a = sub.add_parser("amostra")
    a.add_argument("--html", type=Path, required=True)
    a.add_argument("--saida", type=Path, required=True)
    a.add_argument("--n", type=int, default=200)
    a.add_argument("--semente", type=int, default=0)
    p = sub.add_parser("precisao")
    p.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.comando == "amostra":
        exigir_fora_do_repositorio(args.saida)
        dicionario = _config("dicionario_narrativa.json")["folhas"]
        filtro = _config("narrativa_filtro.json")
        linhas = []
        for arquivo in sorted(args.html.glob("*.html")):
            html = arquivo.read_text(encoding="utf-8")
            linhas += rotular(html, dicionario, filtro, arquivo.stem)
        amostra = amostra_estratificada(linhas, args.n, args.semente)
        escrever_csv(amostra, args.saida)
        print(f"{len(amostra)} frases de {len(linhas)} gravadas")
    else:
        p = precisao(ler_csv(args.csv))
        print(f"precisão: {p['precisao']:.1%} ({p['acertos']} de {p['rotuladas']})")
        for rotulo, r in p["por_rotulo"].items():
            print(f"  {rotulo}: {r['precisao']:.1%} ({r['acertos']} de {r['rotuladas']})")


if __name__ == "__main__":
    main()
