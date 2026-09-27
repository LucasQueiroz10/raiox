"""Leitura de XML de fontes externas (SEC) sem expandir entidades.

Um XML malicioso pode declarar entidades que se multiplicam até estourar a memória
(billion laughs) ou que apontam para arquivos locais e endereços de rede (XXE).
Todo XML baixado passa por aqui.
"""

from lxml import etree


def _parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False,  # entidades ficam como estão, nunca expandidas
        no_network=True,  # nada de buscar DTD ou entidade na rede
        load_dtd=False,
        dtd_validation=False,
        huge_tree=False,  # mantém os limites de profundidade e tamanho do libxml2
    )


def ler_xml(conteudo: bytes) -> etree._Element:
    """Raiz do documento, lida sem resolver entidades nem acessar a rede."""
    return etree.fromstring(conteudo, parser=_parser())  # noqa: S320 - parser endurecido acima
