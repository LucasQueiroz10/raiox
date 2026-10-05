"""Texto do 10-K -> componente N (Narrativa) e escore de exposição NEGATIVA.

Método no espírito de Sautner et al. (2023, JF: exposição climática por termos
em teleconferências) e Hoberg & Phillips (2016, JPE: similaridade de 10-Ks):
fração das frases do Item 1 (Negócios) e Item 7 (MD&A) que citam termos de cada folha.

Exposição negativa: fração das frases do Item 1A (Fatores de risco) que citam
IA junto com termos de ameaça (substituição, disrupção, concorrência de IA).
Fica FORA do simplex (é um escore com sinal), porque uma distribuição que soma
100% não consegue representar quem perde com o tema.

Dicionário em config/dicionario_narrativa.json. Contagem por frase, não por palavra,
para não premiar repetição. NÃO usa rede (recebe o HTML já baixado).

v1.1 (especificação, seção 4): o componente N usa contagens_narrativa, que lê só o negócio atual:
o Item 1 e, no Item 7, a subseção "Results of Operations" (D-09), sem o bloco de safe harbor e sem
frases prospectivas (marcadores em irrae/config/narrativa_filtro.json, D-20). As descrições de
segmentos não entram (D-10): são a mesma evidência do componente A. O Item 1A continua só na
exposição negativa. componente_narrativa_contagens fica como atalho genérico (itens inteiros).
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_ITEM = re.compile(r"^\s*item\s+(1a|1b|1c|1|2|3|4|5|6|7a|7|8|9a|9b|9)\s*[\.\:\-–—]", re.I | re.M)


def extrair_texto(html: str | bytes) -> str:
    sopa = BeautifulSoup(html, "lxml")
    for t in sopa(["script", "style"]):
        t.decompose()
    for oculto in sopa.select('[style*="display:none"]'):  # cabeçalho iXBRL oculto
        oculto.decompose()
    return re.sub(r"[ \t\xa0]+", " ", sopa.get_text("\n"))


def secoes_10k(texto: str) -> dict[str, str]:
    """Divide pelo cabeçalho 'Item X.'; mantém a ocorrência MAIS LONGA de cada item
    (a primeira costuma ser o índice)."""
    marcas = [(m.start(), m.group(1).lower()) for m in _ITEM.finditer(texto)]
    out: dict[str, str] = {}
    for (ini, item), prox in zip(marcas, marcas[1:] + [(len(texto), None)], strict=True):
        trecho = texto[ini : prox[0]]
        if len(trecho) > len(out.get(item, "")):
            out[item] = trecho
    return out


def frases(texto: str) -> list[str]:
    return [f.strip() for f in re.split(r"(?<=[\.\!\?])\s+|\n{2,}", texto) if len(f.strip()) > 20]


def _tem(frase: str, termos: list[str]) -> bool:
    fl = frase.lower()
    return any(re.search(rf"\b{re.escape(t.lower())}\b", fl) for t in termos)


def contar_termos(texto: str, dicionario: dict[str, list[str]]) -> tuple[dict[str, float], int]:
    """Contagem por frase. Uma frase que cita várias folhas específicas é repartida igualmente
    entre elas (soma 1); a folha '*.generica' só recebe a frase se nenhuma folha específica do
    mesmo tema foi citada. Retorna ({folha: contagem}, total de frases)."""
    return contar_frases(frases(texto), dicionario)


def contar_frases(fs: list[str], dicionario: dict[str, list[str]]) -> tuple[dict[str, float], int]:
    """Como contar_termos, sobre frases já separadas (e já filtradas)."""
    genericas = {f for f in dicionario if f.endswith(".generica")}
    cont: dict[str, float] = {}
    for fr in fs:
        especificas = [f for f in dicionario if f not in genericas and _tem(fr, dicionario[f])]
        if especificas:
            for f in especificas:
                cont[f] = cont.get(f, 0.0) + 1.0 / len(especificas)
            continue
        for g in genericas:
            if _tem(fr, dicionario[g]):
                cont[g] = cont.get(g, 0.0) + 1.0
                break
    return cont, len(fs)


def escore_ameaca(
    texto_riscos: str, termos_ia: list[str], termos_ameaca: list[str]
) -> tuple[float, int]:
    """Entre as frases de risco que citam IA, fração que também cita ameaça.
    Retorna (-fração, n_frases_ia)."""
    fs = [f for f in frases(texto_riscos) if _tem(f, termos_ia)]
    if not fs:
        return 0.0, 0
    return -sum(_tem(f, termos_ameaca) for f in fs) / len(fs), len(fs)


def componente_narrativa_contagens(
    html: str | bytes, dicionario: dict[str, list[str]], itens=("1", "7")
) -> tuple[dict[str, int], int]:
    """Atalho: HTML do 10-K -> (contagens por folha, total de frases) nos itens escolhidos,
    pronto para componentes.de_contagens('N_narrativa', ...)."""
    sec = secoes_10k(extrair_texto(html))
    texto = "\n".join(sec.get(i, "") for i in itens)
    return contar_termos(texto, dicionario)


def prospectiva(frase: str, marcadores: list[str]) -> bool:
    """Frase com algum marcador prospectivo (palavra inteira, sem diferenciar maiúsculas)."""
    return _tem(frase, marcadores)


def _eh_titulo(linha: str) -> bool:
    """Linha curta, com letra e sem pontuação final: título ou subtítulo do 10-K."""
    return 0 < len(linha) <= 100 and linha[-1] not in ".!?:;," and any(c.isalpha() for c in linha)


def subsecao_resultados(
    texto_item7: str, titulos_fim: list[str], titulo: str = "results of operations"
) -> str:
    """Texto da subseção "Results of Operations" do Item 7 (D-09), sem o título.

    Começa no primeiro título que contém `titulo` e vai até o primeiro título que contém algum de
    `titulos_fim` (seções irmãs do MD&A, como Liquidity and Capital Resources); subtítulos internos
    (ex.: Net Sales) não encerram. Sem o título, devolve "": nada do MD&A entra no N."""
    linhas = texto_item7.split("\n")
    inicio = next(
        (
            i
            for i, linha in enumerate(linhas)
            if _eh_titulo(linha.strip()) and titulo in linha.lower()
        ),
        None,
    )
    if inicio is None:
        return ""
    fim = next(
        (
            j
            for j in range(inicio + 1, len(linhas))
            if _eh_titulo(linhas[j].strip()) and any(f in linhas[j].lower() for f in titulos_fim)
        ),
        len(linhas),
    )
    return "\n".join(linhas[inicio + 1 : fim])


def sem_safe_harbor(texto: str, termo: str = "forward-looking") -> str:
    """Remove os blocos de safe harbor: de um título que contém `termo` até o próximo título."""
    saida, dentro = [], False
    for linha in texto.split("\n"):
        limpa = linha.strip()
        if _eh_titulo(limpa):
            dentro = termo in limpa.lower()
            if dentro:
                continue
        if not dentro:
            saida.append(linha)
    return "\n".join(saida)


def frases_narrativa(html: str | bytes, filtro: dict) -> list[tuple[str, str]]:
    """Frases que entram no N da v1.1, com o item de origem ("1" ou "7"): Item 1 e a subseção
    Results of Operations, sem safe harbor e sem frases prospectivas."""
    sec = secoes_10k(extrair_texto(html))
    resultados = subsecao_resultados(
        sec.get("7", ""),
        filtro["titulos_que_encerram_resultados"],
        filtro.get("titulo_resultados", "results of operations"),
    )
    saida = []
    for item, texto in (("1", sec.get("1", "")), ("7", resultados)):
        for f in frases(sem_safe_harbor(texto)):
            if not prospectiva(f, filtro["marcadores_prospectivos"]):
                saida.append((item, f))
    return saida


def contagens_narrativa(
    html: str | bytes, dicionario: dict[str, list[str]], filtro: dict
) -> tuple[dict[str, float], int]:
    """Componente N da v1.1: contagens por folha e total de frases, só com o negócio atual,
    pronto para componentes.de_contagens('N_narrativa', ...)."""
    return contar_frases([f for _, f in frases_narrativa(html, filtro)], dicionario)
