"""Construção dos componentes do IrRAE como DISTRIBUIÇÕES (amostras no simplex).

Cada componente devolve amostras X (S x L): S sorteios de "como a empresa se
divide entre as folhas segundo esta fonte". A incerteza de medição e de
mapeamento (ex.: quanto da AWS é IA?) fica nas amostras. O erro da fonte como
medida da exposição verdadeira (kappa) é tratado depois, na fusão.

Distinção importante: componente AUSENTE (sem dado) != componente com ZERO
(dado mostra 0% no tema). Ausente sai da fusão; zero entra e puxa para baixo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .distribuicoes import beta_amostras, dirichlet_amostras
from .taxonomia import Taxonomia


@dataclass
class Componente:
    nome: str
    amostras: np.ndarray | None  # (S, L) ou None se ausente
    status: str = "ok"  # 'ok' | 'ausente'
    fonte: str = ""
    avisos: list[str] = field(default_factory=list)
    papel: dict[str, np.ndarray] | None = None  # papel -> vetor médio (L) da massa mapeada
    cobertura: float = 1.0

    @property
    def ok(self) -> bool:
        return self.status == "ok" and self.amostras is not None

    @property
    def media(self) -> np.ndarray:
        return self.amostras.mean(axis=0)


def ausente(nome: str, motivo: str = "sem dado") -> Componente:
    return Componente(nome=nome, amostras=None, status="ausente", avisos=[motivo])


@dataclass
class LinhaMapeamento:
    """Como uma unidade (segmento, capex, backlog) se divide entre núcleo e folhas.

    frac_ia ~ Beta(media, conc): fração que pertence ao tema.
    split ~ Dirichlet(split_media * split_conc): como essa fração se divide entre as folhas do tema.
    """

    frac_media: float
    frac_conc: float
    split: dict[str, float]
    split_conc: float = 20.0
    papel: str = "nao_informado"

    def amostrar(self, tax: Taxonomia, S: int, rng: np.random.Generator) -> np.ndarray:
        frac = beta_amostras(self.frac_media, self.frac_conc, S, rng)
        split_vec = np.zeros(tax.L)
        for folha, w in self.split.items():
            split_vec[tax.idx(folha)] = w
        if split_vec.sum() == 0:
            split_vec[0] = 1.0
        split_vec /= split_vec.sum()
        sp = dirichlet_amostras(split_vec, self.split_conc, S, rng)
        out = frac[:, None] * sp
        out[:, 0] += 1.0 - frac  # o que não é do tema fica no núcleo
        return out


def de_segmentos(
    nome: str,
    valores: dict[str, float],
    mapeamento: dict[str, LinhaMapeamento],
    tax: Taxonomia,
    S: int,
    rng: np.random.Generator,
    fonte: str = "",
) -> Componente:
    """Receita/lucro por segmento -> composição. Valores negativos contam como zero
    (um segmento com prejuízo não tem 'fatia negativa' da empresa)."""
    avisos = []
    vals = {s: max(0.0, float(v)) for s, v in valores.items()}
    neg = [s for s, v in valores.items() if v < 0]
    if neg:
        avisos.append(f"valores negativos tratados como 0: {neg}")
    total = sum(vals.values())
    if total <= 0:
        return ausente(nome, "soma dos segmentos <= 0")
    X = np.zeros((S, tax.L))
    papeis: dict[str, np.ndarray] = {}
    for seg, v in vals.items():
        if v == 0:
            continue
        linha = mapeamento.get(seg)
        if linha is None:
            avisos.append(f"segmento sem mapeamento -> núcleo: {seg}")
            X[:, 0] += v / total
            continue
        contrib = (v / total) * linha.amostrar(tax, S, rng)
        X += contrib
        m = contrib.mean(axis=0).copy()
        m[0] = 0.0
        papeis[linha.papel] = papeis.get(linha.papel, np.zeros(tax.L)) + m
    return Componente(nome, X, fonte=fonte, avisos=avisos, papel=papeis)


def de_alocacao(
    nome: str,
    linha: LinhaMapeamento,
    tax: Taxonomia,
    S: int,
    rng: np.random.Generator,
    fonte: str = "",
) -> Componente:
    """Um total (ex.: capex) cuja alocação ao tema é elicitada/declarada."""
    return Componente(nome, linha.amostrar(tax, S, rng), fonte=fonte)


def de_receita_futura(
    nome: str,
    receitas: dict[str, float],
    mapeamento: dict[str, LinhaMapeamento],
    backlog: list[tuple[float, LinhaMapeamento]],
    tax: Taxonomia,
    S: int,
    rng: np.random.Generator,
    horizonte=(3.0, 6.0),
    fonte: str = "",
) -> Componente:
    """Carteira contratada vira 'receita futura anual' = receita atual + backlog / H.

    H (anos para realizar o backlog) é incerto ~ Uniforme(horizonte). Assim o
    backlog não vira 100% da empresa só porque os outros negócios não têm backlog.
    """
    if not backlog:
        return ausente(nome, "sem backlog divulgado")
    H = rng.uniform(*horizonte, size=S)
    X = np.zeros((S, tax.L))
    for seg, v in receitas.items():
        v = max(0.0, float(v))
        if v == 0:
            continue
        linha = mapeamento.get(seg)
        comp = linha.amostrar(tax, S, rng) if linha else np.eye(tax.L)[[0] * S]
        X += v * comp
    for valor, linha in backlog:
        X += (valor / H)[:, None] * linha.amostrar(tax, S, rng)
    X /= X.sum(axis=1, keepdims=True)
    return Componente(nome, X, fonte=fonte)


def de_contagens(
    nome: str,
    contagens: dict[str, float],
    total: float,
    tax: Taxonomia,
    S: int,
    rng: np.random.Generator,
    alpha0: float = 0.5,
    fonte: str = "",
) -> Componente:
    """Contagens (patentes, frases do 10-K) -> posterior Dirichlet(contagens + alpha0).

    total = todos os documentos da empresa (o que não é do tema vai para o núcleo).
    total == 0 => AUSENTE (empresa sem patentes não é o mesmo que 0% de patentes de IA).
    Poucas contagens => intervalo largo automaticamente.
    """
    if total <= 0:
        return ausente(nome, "nenhum documento")
    c = np.zeros(tax.L)
    for folha, n in contagens.items():
        c[tax.idx(folha)] += n
    c[0] = max(0.0, total - c[1:].sum())
    return Componente(nome, rng.dirichlet(c + alpha0, size=S), fonte=fonte)


def de_etfs(
    nome: str,
    posicoes: list[tuple[str, str, float]],
    tax: Taxonomia,
    S: int,
    rng: np.random.Generator,
    fonte: str = "",
) -> Componente:
    """Enquadramento de mercado a partir de carteiras de ETFs (N-PORT).

    posicoes: (etf, folha_ou_'nucleo', valor_em_usd_da_empresa_no_etf).
    Composição = dólares da empresa em ETFs de cada folha / dólares em todos os ETFs.
    Usar dólares (não % do ETF) já neutraliza o tamanho da empresa.
    Incerteza: bootstrap sobre os ETFs (poucos ETFs => intervalo largo).
    """
    pos = [(e, a, v) for e, a, v in posicoes if v > 0]
    if not pos:
        return ausente(nome, "empresa não aparece nos ETFs mapeados")
    etfs = sorted({e for e, _, _ in pos})
    M = np.zeros((len(etfs), tax.L))
    for e, a, v in pos:
        M[etfs.index(e), tax.idx(a)] += v
    idx = rng.integers(0, len(etfs), size=(S, len(etfs)))
    X = M[idx].sum(axis=1)
    s = X.sum(axis=1, keepdims=True)
    s[s == 0] = 1.0
    return Componente(nome, X / s, fonte=fonte)


def de_heranca(
    nome: str,
    parceiros: list[tuple[float, np.ndarray]],
    tax: Taxonomia,
    S: int,
    rng: np.random.Generator,
    conc_base: float = 50.0,
    fonte: str = "",
) -> Componente:
    """Exposição herdada de terceiros (cadeia de clientes, participações).

    parceiros: (fração da receita/valor ligada ao parceiro, exposição média do parceiro (L,)).
    cobertura = soma das frações conhecidas;
    cobertura baixa => menos concentração => mais incerteza.
    """
    if not parceiros:
        return ausente(nome, "sem parceiros identificados")
    f = np.array([p[0] for p in parceiros])
    W = np.vstack([p[1] for p in parceiros])
    cobertura = float(min(1.0, f.sum()))
    media = (f[:, None] * W).sum(axis=0) / f.sum()
    X = dirichlet_amostras(media, max(2.0, conc_base * cobertura), S, rng)
    return Componente(nome, X, fonte=fonte, cobertura=cobertura)


def prior_setorial(
    sic: str, cfg: dict, tax: Taxonomia, S: int, rng: np.random.Generator
) -> Componente:
    """Pseudo-componente: o que se espera do setor oficial antes de ver a empresa.

    Amostras = ponto fixo na média do setor (sem 'erro de medição'); toda a incerteza do prior é
    o erro de fonte kappa (componentes.json -> prior_setorial), que representa a heterogeneidade
    das empresas dentro do setor e pode ser reestimado com o universo. Sempre presente;
    domina só quando faltam dados."""
    p = cfg["por_sic"].get(str(sic), cfg["padrao"])
    media = tax.vetor(p["media"])
    return Componente(
        "prior_setorial", np.tile(media, (S, 1)), fonte=f"prior SIC {sic}: {p['descricao']}"
    )
