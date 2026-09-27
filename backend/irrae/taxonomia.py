"""Árvore de temas do IrRAE.

As folhas (incluindo 'nucleo') formam o simplex: para cada empresa, as fatias
somam 1. O peso de um tema é a soma das suas folhas, então a regra
"subtema <= tema" vale por construção (Dirichlet-tree; Minka 1999).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

NUCLEO = "nucleo"


@dataclass(frozen=True)
class Taxonomia:
    folhas: tuple[str, ...]  # ordem fixa das colunas; folhas[0] == 'nucleo'
    tema_de: dict[str, str]  # folha -> tema ('nucleo' -> 'nucleo')
    nomes: dict[str, str]
    genericas: dict[str, str]  # tema -> folha genérica do tema (recebe folhas pequenas)

    @classmethod
    def carregar(cls, caminho: str | Path) -> Taxonomia:
        cfg = json.loads(Path(caminho).read_text(encoding="utf-8"))
        folhas, tema_de, nomes, genericas = (
            [NUCLEO],
            {NUCLEO: NUCLEO},
            {NUCLEO: cfg["nucleo"]["nome"]},
            {},
        )
        for tema, t in cfg["temas"].items():
            nomes[tema] = t["nome"]
            for folha, nome in t["folhas"].items():
                folhas.append(folha)
                tema_de[folha] = tema
                nomes[folha] = nome
                if folha.endswith(".generica"):
                    genericas[tema] = folha
        return cls(tuple(folhas), tema_de, nomes, genericas)

    @property
    def L(self) -> int:
        return len(self.folhas)

    @property
    def temas(self) -> list[str]:
        return sorted({t for f, t in self.tema_de.items() if t != NUCLEO})

    def idx(self, folha: str) -> int:
        return self.folhas.index(folha)

    def indices_do_tema(self, tema: str) -> list[int]:
        return [i for i, f in enumerate(self.folhas) if self.tema_de[f] == tema]

    def vetor(self, pesos: dict[str, float], resto_no_nucleo: bool = True) -> np.ndarray:
        """Converte {folha: fatia} em vetor no simplex; o que falta vai para o núcleo."""
        v = np.zeros(self.L)
        for f, p in pesos.items():
            v[self.idx(f)] += p
        if resto_no_nucleo:
            v[0] += max(0.0, 1.0 - v.sum())
        s = v.sum()
        return v / s if s > 0 else v

    def agregar_temas(self, x: np.ndarray) -> dict[str, np.ndarray]:
        """Soma as folhas de cada tema. x tem shape (..., L)."""
        out = {NUCLEO: x[..., 0]}
        for t in self.temas:
            out[t] = x[..., self.indices_do_tema(t)].sum(axis=-1)
        return out
