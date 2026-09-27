"""Regras de limpeza e estabilidade aplicadas depois da fusão.

1. Percepção sozinha não cria tema: folha sem suporte de fontes não-percepção vai para o núcleo.
2. Limiar hierárquico com histerese:
   - tema com total abaixo do limiar -> todo o tema vai para o núcleo;
   - subtema abaixo do limiar, dentro de um tema que passou -> vai para a folha genérica do tema
     (não para o núcleo; assim três subtemas de 4% não apagam um tema de 12%);
   - limiar de entrada (ex. 6%) > limiar de saída (ex. 4%): quem já estava ativo só sai abaixo
     da saída. Evita que a área entre e saia a cada trimestre.
3. Selo de qualidade objetivo: pela largura do intervalo de 90%, não aplicado a todos.
As movimentações são feitas coluna a coluna em TODAS as amostras, preservando soma = 1.
"""

from __future__ import annotations

import numpy as np

from .taxonomia import Taxonomia


def _mover(F: np.ndarray, de: int, para: int) -> None:
    F[:, para] += F[:, de]
    F[:, de] = 0.0


def aplicar_regras(
    F: np.ndarray,
    tax: Taxonomia,
    suporte_nao_percepcao: np.ndarray,
    cfg: dict,
    ativos_anteriores: set[str] | None = None,
    suporte_percepcao: np.ndarray | None = None,
) -> tuple[np.ndarray, set[str], list[str]]:
    """suporte_*: contribuição média (peso x média) das fontes de cada pilar para cada folha.
    Sem suporte_percepcao informado, assume que toda a massa sem suporte 'duro'
    veio da percepção."""
    F = F.copy()
    ant = ativos_anteriores or set()
    log: list[str] = []
    sp = suporte_percepcao if suporte_percepcao is not None else F.mean(axis=0)
    for i, folha in enumerate(tax.folhas[1:], start=1):
        if (
            F[:, i].mean() > 0
            and suporte_nao_percepcao[i] < cfg["suporte_minimo_nao_percepcao"]
            and sp[i] > suporte_nao_percepcao[i]
        ):
            log.append(
                f"{folha}: só percepção sustenta (dura={suporte_nao_percepcao[i]:.3f}, "
                f"percepção={sp[i]:.3f}) -> núcleo"
            )
            _mover(F, i, 0)
    ativos: set[str] = set()
    for tema in tax.temas:
        idx = tax.indices_do_tema(tema)
        total = F[:, idx].sum(axis=1).mean()
        lim_t = cfg["limiar_saida"] if tema in ant else cfg["limiar_entrada"]
        if total < lim_t:
            if total > 0:
                log.append(f"tema {tema}: {total:.3f} < {lim_t:.2f} -> núcleo")
            for i in idx:
                _mover(F, i, 0)
            continue
        ativos.add(tema)
        gen = tax.genericas.get(tema)
        gi = tax.idx(gen) if gen else None
        for i in idx:
            if i == gi:
                continue
            folha = tax.folhas[i]
            lim = cfg["limiar_saida"] if folha in ant else cfg["limiar_entrada"]
            m = F[:, i].mean()
            if m < lim:
                if m > 0:
                    log.append(f"{folha}: {m:.3f} < {lim:.2f} -> {gen or 'núcleo'}")
                _mover(F, i, gi if gi is not None else 0)
            else:
                ativos.add(folha)
        if gi is not None and F[:, gi].mean() > 0:
            ativos.add(gen)
    return F, ativos, log


def selo(
    F: np.ndarray, tax: Taxonomia, ativos: set[str], n_reais: int, cfg: dict
) -> tuple[str, float]:
    """'alta' | 'media' | 'preliminar' pela maior largura (P95-P5) entre folhas e temas ativos."""
    larguras = []
    for i, f in enumerate(tax.folhas):
        if f in ativos:
            larguras.append(np.quantile(F[:, i], 0.95) - np.quantile(F[:, i], 0.05))
    for t, x in tax.agregar_temas(F).items():
        if t in ativos:
            larguras.append(np.quantile(x, 0.95) - np.quantile(x, 0.05))
    lmax = float(max(larguras)) if larguras else 0.0
    if n_reais < cfg["min_componentes_reais"]:
        return "preliminar", lmax
    if lmax < cfg["selo_largura_alta"]:
        return "alta", lmax
    if lmax < cfg["selo_largura_media"]:
        return "media", lmax
    return "preliminar", lmax
