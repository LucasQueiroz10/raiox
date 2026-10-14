"""Pacote anual sintético do Informe Mensal de FII da CVM (latin-1, `;`), para os testes do leitor.
Os nomes dos arquivos e das colunas são os da CVM; os dados são inventados."""

import csv
import io
import zipfile

from ingest.cvm_fii import COLUNAS
from tests.ingest.cda_sintetico import mascara

# Contato do administrador, que vem na tabela geral e o leitor nunca guarda.
EMAIL_DO_ADMINISTRADOR = "contato@administradora.exemplo"


class AnoFII:
    def __init__(self, ano: str = "2026") -> None:
        self.ano = ano
        self.linhas: dict[str, list[dict[str, str]]] = {tabela: [] for tabela in COLUNAS}

    def fundo(
        self,
        cnpj: str,
        *,
        segmento: str = "Logística",
        isin: str = "",
        data: str | None = None,
        versao: str = "1",
        nome: str = "FII SINTETICO",
        carteira: bool = True,
        **ativo_passivo: str,
    ) -> AnoFII:
        """Um informe do fundo. `ativo_passivo` dá os valores da carteira (ex.: CRI_CRA="700");
        Total_Investido, se não vier, é a soma deles. Sem `carteira`, falta o quadro de ativos."""
        comum = {
            "CNPJ_Fundo_Classe": mascara(cnpj),
            "Data_Referencia": data or f"{self.ano}-08-01",
            "Versao": versao,
        }
        self._linha(
            "geral",
            comum
            | {
                "Tipo_Fundo_Classe": "Classe",
                "Nome_Fundo_Classe": nome,
                "Codigo_ISIN": isin,
                "Segmento_Atuacao": segmento,
                "Mercado_Negociacao_Bolsa": "S",
                "Email": EMAIL_DO_ADMINISTRADOR,
            },
        )
        if carteira:
            total = str(sum(int(v) for v in ativo_passivo.values()))
            self._linha("ativo_passivo", comum | {"Total_Investido": total} | ativo_passivo)
        return self

    def _linha(self, tabela: str, campos: dict[str, str]) -> None:
        linha = dict.fromkeys(COLUNAS[tabela], "")
        linha.update(campos)
        assert set(linha) == set(COLUNAS[tabela]), f"coluna fora da tabela {tabela}"
        self.linhas[tabela].append(linha)

    def zip(
        self, *, sem: tuple[str, ...] = (), colunas: dict[str, tuple[str, ...]] | None = None
    ) -> io.BytesIO:
        trocas = colunas or {}
        saida = io.BytesIO()
        with zipfile.ZipFile(saida, "w") as z:
            for tabela, linhas in self.linhas.items():
                if tabela in sem:
                    continue
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
                nome = f"inf_mensal_fii_{tabela}_{self.ano}.csv"
                z.writestr(nome, texto.getvalue().encode("latin-1"))
            # O complemento (cotistas e rentabilidade) existe no pacote, mas não é lido.
            z.writestr(f"inf_mensal_fii_complemento_{self.ano}.csv", "NAO LIDO\r\n")
        saida.seek(0)
        return saida
