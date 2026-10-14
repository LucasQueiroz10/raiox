"""Pacote anual sintético do FCA da CVM (latin-1, `;`), para os testes do leitor. Os nomes dos
arquivos e das colunas são os da CVM; os dados são inventados."""

import csv
import io
import zipfile

from ingest.cvm_fca import COLUNAS
from tests.ingest.cda_sintetico import mascara

# Os outros arquivos do pacote. Têm dados pessoais (DRI, acionistas, endereço) e o leitor nunca os
# abre: aqui vão com um conteúdo qualquer, só para o zip ter os mesmos nomes que o da CVM.
OUTROS = (
    "fca_cia_aberta", "fca_cia_aberta_auditor", "fca_cia_aberta_canal_divulgacao",
    "fca_cia_aberta_departamento_acionistas", "fca_cia_aberta_dri", "fca_cia_aberta_endereco",
    "fca_cia_aberta_escriturador", "fca_cia_aberta_pais_estrangeiro_negociacao",
)  # fmt: skip


class AnoSintetico:
    def __init__(self, ano: str = "2026") -> None:
        self.ano = ano
        self.linhas: dict[str, list[dict[str, str]]] = {tabela: [] for tabela in COLUNAS}

    def companhia(
        self,
        cnpj: str,
        *tickers: str,
        versao: str = "1",
        data: str | None = None,
        setor: str = "Setor Sintético",
        nome: str = "COMPANHIA SINTETICA S.A.",
        documento: str | None = None,
        **valor_mobiliario: str,
    ) -> AnoSintetico:
        """Uma versão do formulário da companhia, com uma linha de valor mobiliário por ticker
        (ações ordinárias, salvo `Valor_Mobiliario` em `valor_mobiliario`)."""
        documento = documento or f"{cnpj}-{self.ano}-{versao}"
        comum = {
            "CNPJ_Companhia": mascara(cnpj),
            "Data_Referencia": data or f"{self.ano}-01-01",
            "Versao": versao,
            "ID_Documento": documento,
            "Nome_Empresarial": nome,
        }
        self._linha("geral", comum | {"Setor_Atividade": setor, "Situacao_Registro_CVM": "Ativo"})
        for ticker in tickers:
            campos = {"Valor_Mobiliario": "Ações Ordinárias", "Mercado": "Bolsa"}
            self._linha(
                "valor_mobiliario",
                comum | campos | {"Codigo_Negociacao": ticker} | valor_mobiliario,
            )
        return self

    def _linha(self, tabela: str, campos: dict[str, str]) -> None:
        linha = dict.fromkeys(COLUNAS[tabela], "")
        linha.update(campos)
        assert set(linha) == set(COLUNAS[tabela]), f"coluna fora da tabela {tabela}"
        self.linhas[tabela].append(linha)

    def zip(self, *, colunas: dict[str, tuple[str, ...]] | None = None) -> io.BytesIO:
        trocas = colunas or {}
        saida = io.BytesIO()
        with zipfile.ZipFile(saida, "w") as z:
            for tabela, linhas in self.linhas.items():
                texto = io.StringIO()
                escritor = csv.DictWriter(
                    texto,
                    trocas.get(tabela, COLUNAS[tabela]),
                    delimiter=";",
                    lineterminator="\r\n",
                    extrasaction="ignore",
                )
                escritor.writeheader()
                escritor.writerows(linhas)
                nome = f"fca_cia_aberta_{tabela}_{self.ano}.csv"
                z.writestr(nome, texto.getvalue().encode("latin-1"))
            for outro in OUTROS:
                z.writestr(f"{outro}_{self.ano}.csv", "CONTEUDO QUE O LEITOR NAO ABRE\r\n")
        saida.seek(0)
        return saida
