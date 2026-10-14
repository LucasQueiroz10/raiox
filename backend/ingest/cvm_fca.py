"""Leitor do FCA da CVM: o Formulário Cadastral das companhias abertas (matriz de dados, fonte 4).

Liga cada ação da B3 à companhia emissora e traz o setor de atividade dela (ADR 0008, etapa 4).
Do pacote de cada ano, lê só duas tabelas, nas condições em que o M1 liberou a fonte (12/10/2026):

- `geral`: nome, setor de atividade e situação de cada companhia;
- `valor_mobiliario`: os códigos de negociação na B3 (tickers) de cada valor mobiliário.

Os outros arquivos do pacote (DRI, departamento de acionistas, endereço e outros) trazem nome, CPF,
e-mail e telefone de pessoas e **nunca são abertos** (LGPD).

Regras:

- Cada companhia entrega uma versão nova do formulário quando algo muda. Vale a mais recente,
  juntando os anos: maior data de referência e, nela, maior versão. Os tickers vêm só dessa versão.
- O código de negociação é preenchido pela própria companhia e às vezes vem errado (casos reais:
  "000000", "4030", "ADR"). Só entram códigos no formato da B3: raiz de 4 caracteres começando
  por letra (o código do emissor) e 1 ou 2 dígitos (ex.: PETR4, BPAC11, B3SA3), de ações
  ordinárias, preferenciais ou units ainda negociadas. As companhias com código errado entram pela
  curadoria manual (cargas/curadoria/).
- A raiz (os 4 primeiros caracteres) é o código do emissor na B3: PETR3, PETR4 e o ISIN
  BRPETRACNPR6 têm a mesma raiz. Por ela, qualquer ticker ou ISIN brasileiro chega à companhia. É
  uma regra exata, não "o nome mais parecido" (ADR 0005, seção 4). Raiz ou ticker que aparece em
  mais de uma companhia não é usado.
"""

import re
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from ingest import arquivos_cvm
from ingest.arquivos_cvm import TICKER_B3, LayoutInesperado, linhas_csv

# Colunas das duas tabelas lidas, como a CVM publica (conferidas no pacote de 2026, em 13/10/2026).
COLUNAS: dict[str, tuple[str, ...]] = {
    "geral": (
        "CNPJ_Companhia", "Data_Referencia", "Versao", "ID_Documento", "Nome_Empresarial",
        "Data_Nome_Empresarial", "Nome_Empresarial_Anterior", "Data_Constituicao", "Codigo_CVM",
        "Data_Registro_CVM", "Categoria_Registro_CVM", "Data_Categoria_Registro_CVM",
        "Situacao_Registro_CVM", "Data_Situacao_Registro_CVM", "Pais_Origem",
        "Pais_Custodia_Valores_Mobiliarios", "Setor_Atividade", "Descricao_Atividade",
        "Situacao_Emissor", "Data_Situacao_Emissor", "Especie_Controle_Acionario",
        "Data_Especie_Controle_Acionario", "Dia_Encerramento_Exercicio_Social",
        "Mes_Encerramento_Exercicio_Social", "Data_Alteracao_Exercicio_Social", "Pagina_Web",
    ),
    "valor_mobiliario": (
        "CNPJ_Companhia", "Data_Referencia", "Versao", "ID_Documento", "Nome_Empresarial",
        "Valor_Mobiliario", "Sigla_Classe_Acao_Preferencial", "Classe_Acao_Preferencial",
        "Codigo_Negociacao", "Composicao_BDR_Unit", "Mercado", "Sigla_Entidade_Administradora",
        "Entidade_Administradora", "Data_Inicio_Negociacao", "Data_Fim_Negociacao", "Segmento",
        "Data_Inicio_Listagem", "Data_Fim_Listagem",
    ),
}  # fmt: skip

TIPOS_DE_ACAO = frozenset({"Ações Ordinárias", "Ações Preferenciais", "Units"})
_TABELA_GERAL = re.compile(r"fca_cia_aberta_geral_(\d{4})\.csv")


@dataclass(frozen=True, slots=True)
class Companhia:
    cnpj: str
    nome: str
    setor: str | None  # setor de atividade, com o nome usado pela CVM
    situacao: str  # situação do registro na CVM (ex.: "Ativo", "Cancelado")


@dataclass(frozen=True, slots=True)
class CadastroFCA:
    companhias: dict[str, Companhia]  # por CNPJ, na versão mais recente do formulário
    cnpj_do_ticker: dict[str, str]  # ticker de ação negociada -> CNPJ da companhia
    cnpj_da_raiz: dict[str, str]  # raiz de 4 caracteres (código do emissor na B3) -> CNPJ
    descartes: Counter[str]  # linhas deixadas de fora, por motivo; nunca o conteúdo


@dataclass(frozen=True, slots=True)
class _Versao:
    chave: tuple[str, int, str]  # (data de referência, versão, documento): a maior vale
    companhia: Companhia
    documento: str


def ler_fca(pacotes: Iterable[Path | IO[bytes]]) -> CadastroFCA:
    """Lê os pacotes anuais do FCA (ex.: fca_cia_aberta_2024.zip a fca_cia_aberta_2026.zip)."""
    versoes: dict[str, _Versao] = {}
    tickers_do_documento: dict[str, list[dict[str, str]]] = defaultdict(list)
    descartes: Counter[str] = Counter()
    for pacote in pacotes:
        with zipfile.ZipFile(pacote) as z:
            ano = _ano_do_pacote(z.namelist())
            for linha in linhas_csv(z, f"fca_cia_aberta_geral_{ano}.csv", COLUNAS["geral"]):
                versao = _versao(linha)
                if versao is None:
                    descartes["cnpj_invalido"] += 1
                    continue
                atual = versoes.get(versao.companhia.cnpj)
                if atual is None or versao.chave > atual.chave:
                    versoes[versao.companhia.cnpj] = versao
            nome = f"fca_cia_aberta_valor_mobiliario_{ano}.csv"
            for linha in linhas_csv(z, nome, COLUNAS["valor_mobiliario"]):
                tickers_do_documento[linha["ID_Documento"].strip()].append(linha)

    por_ticker: dict[str, set[str]] = defaultdict(set)
    por_raiz: dict[str, set[str]] = defaultdict(set)
    for cnpj, versao in versoes.items():
        for linha in tickers_do_documento[versao.documento]:
            ticker = linha["Codigo_Negociacao"].strip().upper()
            if not ticker:
                continue
            if not TICKER_B3.fullmatch(ticker):
                descartes["codigo_fora_do_formato"] += 1
                continue
            negociada = not linha["Data_Fim_Negociacao"].strip()
            if linha["Valor_Mobiliario"].strip() in TIPOS_DE_ACAO and negociada:
                por_ticker[ticker].add(cnpj)
                por_raiz[ticker[:4]].add(cnpj)

    descartes["ticker_com_duas_companhias"] += sum(1 for c in por_ticker.values() if len(c) > 1)
    descartes["raiz_com_duas_companhias"] += sum(1 for c in por_raiz.values() if len(c) > 1)
    return CadastroFCA(
        companhias={cnpj: v.companhia for cnpj, v in versoes.items()},
        cnpj_do_ticker={t: next(iter(c)) for t, c in por_ticker.items() if len(c) == 1},
        cnpj_da_raiz={r: next(iter(c)) for r, c in por_raiz.items() if len(c) == 1},
        descartes=+descartes,
    )


def _ano_do_pacote(nomes: list[str]) -> str:
    anos = {m.group(1) for n in nomes if (m := _TABELA_GERAL.fullmatch(n))}
    if len(anos) != 1:
        raise LayoutInesperado("o pacote precisa ter uma tabela fca_cia_aberta_geral_AAAA.csv")
    return anos.pop()


def _versao(linha: dict[str, str]) -> _Versao | None:
    cnpj = arquivos_cvm.cnpj(linha["CNPJ_Companhia"])
    if cnpj is None:
        return None
    versao = linha["Versao"].strip()
    documento = linha["ID_Documento"].strip()
    companhia = Companhia(
        cnpj=cnpj,
        nome=linha["Nome_Empresarial"].strip(),
        setor=linha["Setor_Atividade"].strip() or None,
        situacao=linha["Situacao_Registro_CVM"].strip(),
    )
    chave = (linha["Data_Referencia"].strip(), int(versao) if versao.isdigit() else 0, documento)
    return _Versao(chave, companhia, documento)
