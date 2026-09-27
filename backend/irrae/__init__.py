"""IrRAE: exposição de empresas a temas (nichos/subnichos) com quantificação de incerteza.

Protótipo v1. Ver CLAUDE.md (guia de continuação) e FONTES.md (referências e bases públicas).
"""

from .componentes import Componente, LinhaMapeamento, ausente
from .modelo import calcular_empresa, carregar_config, kappas_prior
from .taxonomia import NUCLEO, Taxonomia

__all__ = [
    "NUCLEO",
    "Taxonomia",
    "Componente",
    "LinhaMapeamento",
    "ausente",
    "calcular_empresa",
    "carregar_config",
    "kappas_prior",
]
