"""Zip sintético no formato do CDA da CVM (latin-1, separador `;`, CNPJ com máscara), para os
testes do leitor. Os nomes dos arquivos e das colunas são os da CVM; os dados são inventados."""

import csv
import io
import zipfile
from decimal import Decimal

from ingest.cvm_cda import COLUNAS, nome_do_arquivo

MES = "202608"
DATA = "2026-08-31"


def mascara(cnpj: str) -> str:
    """Põe a máscara do CDA (99.999.999/9999-99) num CNPJ de 14 caracteres."""
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


class MesSintetico:
    """Monta as linhas de cada arquivo do mês e devolve o zip.

    Cada linha começa com as colunas em branco; o teste preenche só o que importa.
    """

    def __init__(self, mes: str = MES) -> None:
        self.mes = mes
        self.linhas: dict[str, list[dict[str, str]]] = {arquivo: [] for arquivo in COLUNAS}

    def patrimonio(self, fundo: str, valor: str, nome: str = "FUNDO SINTETICO") -> MesSintetico:
        return self._linha("fi_PL", fundo, {"DENOM_SOCIAL": nome, "VL_PATRIM_LIQ": valor})

    def aplicacao(
        self, arquivo: str, fundo: str, tp_aplic: str, valor: str, **campos: str
    ) -> MesSintetico:
        """Uma linha de aplicação. No arquivo dos ETFs (`fie`), passe VL_PATRIM_LIQ."""
        return self._linha(
            arquivo,
            fundo,
            {"TP_APLIC": tp_aplic, "VL_MERC_POS_FINAL": valor, **campos},
        )

    def _linha(self, arquivo: str, fundo: str, campos: dict[str, str]) -> MesSintetico:
        linha = dict.fromkeys(COLUNAS[arquivo], "")
        linha.update(
            {"TP_FUNDO_CLASSE": "CLASSES - FIF", "CNPJ_FUNDO_CLASSE": mascara(fundo)},
            DT_COMPTC=DATA,
        )
        linha.update(campos)
        desconhecidas = set(linha) - set(COLUNAS[arquivo])
        assert not desconhecidas, f"coluna fora do arquivo {arquivo}: {desconhecidas}"
        self.linhas[arquivo].append(linha)
        return self

    def zip(
        self,
        *,
        sem: tuple[str, ...] = (),
        extras: tuple[str, ...] = (),
        colunas: dict[str, tuple[str, ...]] | None = None,
    ) -> io.BytesIO:
        """O zip do mês. `sem` tira arquivos, `extras` acrescenta arquivos vazios e `colunas`
        troca o cabeçalho de um arquivo (para os testes de mudança de layout)."""
        trocas = colunas or {}
        saida = io.BytesIO()
        with zipfile.ZipFile(saida, "w") as z:
            for arquivo, linhas in self.linhas.items():
                if arquivo in sem:
                    continue
                cabecalho = trocas.get(arquivo, COLUNAS[arquivo])
                texto = io.StringIO()
                escritor = csv.DictWriter(
                    texto, cabecalho, delimiter=";", lineterminator="\r\n", extrasaction="ignore"
                )
                escritor.writeheader()
                escritor.writerows(linhas)
                z.writestr(nome_do_arquivo(arquivo, self.mes), texto.getvalue().encode("latin-1"))
            for nome in extras:
                z.writestr(nome, b"")
        saida.seek(0)
        return saida


def peso(valor: str, patrimonio: str) -> Decimal:
    return Decimal(valor) / Decimal(patrimonio)
