"""Leitor do Informe Mensal de FII da CVM: ISIN, nome e tipo de cada fundo imobiliário.

Fonte liberada pelo M1 em 13/10/2026 (CVM, dados abertos, licença ODbL, como o CDA). Os FIIs não
têm composição no CDA; com este informe eles aparecem no raio-x como "Fundos imobiliários", com o
tipo, em vez de "não aberto" (ADR 0008, etapa 4).

Do pacote de cada ano, lê duas tabelas:

- `geral`: CNPJ da classe, nome, ISIN e o segmento de atuação que o próprio fundo declara. A
  tabela também traz endereço, telefone e e-mail do administrador: essas colunas não são usadas
  nem guardadas;
- `ativo_passivo`: a carteira do fundo por tipo de ativo.

A tabela `complemento` (número de cotistas, rentabilidade) não é aberta. Vale o informe mais recente
de cada fundo, juntando os anos: maior data de referência e, nela, maior versão.

O ISIN liga o ticker do usuário ao fundo: a raiz do ISIN (os 4 caracteres depois do país) é o
código do emissor na B3, o mesmo do ticker (ex.: HGLG11 e BRHGLGCTF004).

**Regra do tipo** (decisão de 13/10/2026). Só dados da CVM: a coluna `Classificacao_Anbima` do
cadastro de fundos fica de fora de propósito (ficha FP-37 do M1: não usar a ANBIMA).

1. Do que o fundo investiu, sem o caixa (`Total_Investido`), três grupos:
   - **tijolo:** imóveis, terrenos e direitos sobre imóveis (`Direitos_Bens_Imoveis`, que é o
     subtotal desses itens) e participações em empresas donas de imóveis;
   - **papel:** CRI, CRA, LCI, LCA, letras hipotecárias e LIG;
   - **fundo de fundos:** cotas de outros FIIs.

   O grupo com **mais da metade** do investido define o tipo. Sem grupo com mais da metade, ou sem
   carteira informada, o fundo fica **genérico** ("Fundo imobiliário"). Com os informes de 2026,
   subir o limite para 60% ou 70% muda pouco: a regra não depende de um corte fino.
2. Só no tijolo, o segmento que o fundo declara: Logística, Escritórios, Shoppings, Residencial,
   Hospital, Varejo, Hotel ou Educacional. "Multicategoria", "Outros" ou vazio: tijolo em vários
   segmentos (sem segmento). Papel e fundo de fundos não levam segmento: o que declaram é o
   segmento dos papéis ou dos fundos que compram, e confundiria.
"""

import re
import zipfile
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import IO

from app.core.composicao import TipoFII
from ingest import arquivos_cvm
from ingest.arquivos_cvm import LayoutInesperado, linhas_csv

# Colunas das duas tabelas lidas, como a CVM publica (conferidas no pacote de 2026, em 13/10/2026).
COLUNAS: dict[str, tuple[str, ...]] = {
    "geral": (
        "Tipo_Fundo_Classe", "CNPJ_Fundo_Classe", "Data_Referencia", "Versao", "Data_Entrega",
        "Nome_Fundo_Classe", "Data_Funcionamento", "Publico_Alvo", "Codigo_ISIN",
        "Quantidade_Cotas_Emitidas", "Fundo_Exclusivo", "Cotistas_Vinculo_Familiar", "Mandato",
        "Segmento_Atuacao", "Tipo_Gestao", "Prazo_Duracao", "Data_Prazo_Duracao",
        "Encerramento_Exercicio_Social", "Mercado_Negociacao_Bolsa", "Mercado_Negociacao_MBO",
        "Mercado_Negociacao_MB", "Entidade_Administradora_BVMF", "Entidade_Administradora_CETIP",
        "Nome_Administrador", "CNPJ_Administrador", "Logradouro", "Numero", "Complemento",
        "Bairro", "Cidade", "Estado", "CEP", "Telefone1", "Telefone2", "Telefone3", "Site",
        "Email",
    ),
    "ativo_passivo": (
        "CNPJ_Fundo_Classe", "Data_Referencia", "Versao", "Total_Necessidades_Liquidez",
        "Disponibilidades", "Titulos_Publicos", "Titulos_Privados", "Fundos_Renda_Fixa",
        "Total_Investido", "Direitos_Bens_Imoveis", "Terrenos", "Imoveis_Renda_Acabados",
        "Imoveis_Renda_Construcao", "Imoveis_Venda_Acabados", "Imoveis_Venda_Construcao",
        "Outros_Direitos_Reais", "Acoes", "Debentures", "Bonus_Subscricao",
        "Certificados_Deposito_Valores_Mobiliarios", "Cedulas_Debentures", "Fundo_Acoes", "FIP",
        "FII", "FDIC", "Outras_Cotas_FI", "Notas_Promissorias", "Acoes_Sociedades_Atividades_FII",
        "Cotas_Sociedades_Atividades_FII", "CEPAC", "CRI", "CRI_CRA", "Letras_Hipotecarias", "LCI",
        "LCI_LCA", "LIG", "Outros_Valores_Mobliarios", "Valores_Receber",
        "Contas_Receber_Aluguel", "Contas_Receber_Venda_Imoveis", "Outros_Valores_Receber",
        "Rendimentos_Distribuir", "Taxa_Administracao_Pagar", "Taxa_Performance_Pagar",
        "Obrigacoes_Aquisicao_Imoveis", "Adiantamento_Venda_Imoveis", "Adiantamento_Alugueis",
        "Obrigacoes_Securitizacao_Recebiveis", "Instrumentos_Financeiros_Derivativos",
        "Provisoes_Contigencias", "Outros_Valores_Pagar", "Total_Passivo",
    ),
}  # fmt: skip


# Colunas de cada grupo no quadro de ativos. CRI e LCI são as colunas antigas, hoje vazias (os
# valores vêm em CRI_CRA e LCI_LCA, conferido em 2026): somar as duas não conta nada em dobro.
_GRUPOS: dict[TipoFII, tuple[str, ...]] = {
    TipoFII.TIJOLO: (
        "Direitos_Bens_Imoveis", "Acoes_Sociedades_Atividades_FII",
        "Cotas_Sociedades_Atividades_FII",
    ),
    TipoFII.PAPEL: ("CRI", "CRI_CRA", "LCI", "LCI_LCA", "Letras_Hipotecarias", "LIG"),
    TipoFII.FUNDO_DE_FUNDOS: ("FII",),
}  # fmt: skip
LIMITE = Decimal("0.5")  # mais da metade do investido
SEGMENTOS_DE_TIJOLO = frozenset(
    {"Logística", "Escritórios", "Shoppings", "Residencial", "Hospital", "Varejo", "Hotel",
     "Educacional"}
)  # fmt: skip
_TABELA_GERAL = re.compile(r"inf_mensal_fii_geral_(\d{4})\.csv")


@dataclass(frozen=True, slots=True)
class FundoImobiliario:
    cnpj: str
    nome: str
    isin: str | None  # None: sem ISIN ou ISIN inválido
    tipo: TipoFII
    segmento: str | None  # só no tijolo; None: vários segmentos
    data_referencia: date  # do informe usado


@dataclass(frozen=True, slots=True)
class InformesFII:
    fundos: dict[str, FundoImobiliario]  # por CNPJ da classe
    descartes: Counter[str]  # linhas deixadas de fora, por motivo; nunca o conteúdo


def classificar(carteira: Mapping[str, str] | None, segmento: str) -> tuple[TipoFII, str | None]:
    """O tipo e o segmento do FII pela regra do módulo. `carteira` é a linha do quadro de ativos
    (None: o fundo não informou)."""
    tipo = _tipo(carteira)
    segmento = segmento.strip()
    if tipo is TipoFII.TIJOLO and segmento in SEGMENTOS_DE_TIJOLO:
        return tipo, segmento
    return tipo, None


def _tipo(carteira: Mapping[str, str] | None) -> TipoFII:
    if carteira is None:
        return TipoFII.GENERICO
    total = arquivos_cvm.valor(carteira["Total_Investido"]) or Decimal(0)
    if total <= 0:
        return TipoFII.GENERICO
    for tipo, colunas in _GRUPOS.items():
        parte = sum((arquivos_cvm.valor(carteira[c]) or Decimal(0) for c in colunas), Decimal(0))
        if parte / total > LIMITE:
            return tipo  # só um grupo pode ter mais da metade
    return TipoFII.GENERICO


def ler_informes_fii(pacotes: Iterable[Path | IO[bytes]]) -> InformesFII:
    """Lê os pacotes anuais do informe (ex.: inf_mensal_fii_2025.zip e inf_mensal_fii_2026.zip)."""
    # Por CNPJ: a chave (data, versão) do informe mais recente e as linhas das duas tabelas.
    gerais: dict[str, tuple[tuple[str, int], dict[str, str]]] = {}
    carteiras: dict[tuple[str, str, int], dict[str, str]] = {}
    descartes: Counter[str] = Counter()
    for pacote in pacotes:
        with zipfile.ZipFile(pacote) as z:
            ano = _ano_do_pacote(z.namelist())
            for linha in linhas_csv(z, f"inf_mensal_fii_geral_{ano}.csv", COLUNAS["geral"]):
                chave = _chave(linha)
                if chave is None:
                    descartes["cnpj_invalido"] += 1
                    continue
                cnpj, data, versao = chave
                atual = gerais.get(cnpj)
                if atual is None or (data, versao) > atual[0]:
                    gerais[cnpj] = ((data, versao), linha)
            nome = f"inf_mensal_fii_ativo_passivo_{ano}.csv"
            for linha in linhas_csv(z, nome, COLUNAS["ativo_passivo"]):
                chave = _chave(linha)
                if chave is not None:
                    carteiras[chave] = linha

    fundos = {}
    for cnpj, ((data, versao), linha) in gerais.items():
        try:
            data_referencia = date.fromisoformat(data)
        except ValueError:
            descartes["data_invalida"] += 1
            continue
        tipo, segmento = classificar(carteiras.get((cnpj, data, versao)), linha["Segmento_Atuacao"])
        isin = arquivos_cvm.isin_permitido(linha["Codigo_ISIN"]) if linha["Codigo_ISIN"] else None
        if linha["Codigo_ISIN"].strip() and isin is None:
            descartes["isin_invalido"] += 1
        fundos[cnpj] = FundoImobiliario(
            cnpj=cnpj,
            nome=linha["Nome_Fundo_Classe"].strip(),
            isin=isin,
            tipo=tipo,
            segmento=segmento,
            data_referencia=data_referencia,
        )
    return InformesFII(fundos=fundos, descartes=+descartes)


def _ano_do_pacote(nomes: list[str]) -> str:
    anos = {m.group(1) for n in nomes if (m := _TABELA_GERAL.fullmatch(n))}
    if len(anos) != 1:
        raise LayoutInesperado("o pacote precisa ter uma tabela inf_mensal_fii_geral_AAAA.csv")
    return anos.pop()


def _chave(linha: dict[str, str]) -> tuple[str, str, int] | None:
    """(CNPJ, data de referência, versão) do informe, para achar o mais recente e juntar as duas
    tabelas do mesmo informe."""
    cnpj = arquivos_cvm.cnpj(linha["CNPJ_Fundo_Classe"])
    if cnpj is None:
        return None
    versao = linha["Versao"].strip()
    return cnpj, linha["Data_Referencia"].strip(), int(versao) if versao.isdigit() else 0
