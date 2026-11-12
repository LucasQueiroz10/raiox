// Textos de tela, copiados literalmente de docs/textos_telas.md, seção "Vitrine" (ADR 0009).
// Nenhuma palavra muda aqui: para mudar um texto, mude o documento e copie de novo.
// O textos.test.ts confere cada um contra o documento, letra por letra.

export const textos = {
  // Vitrine > Navegação e moldura
  "vitrine.marca": "Sagital",
  "vitrine.nav.inicio": "Início",
  "vitrine.nav.carteiras": "Carteiras",
  "vitrine.nav.metodologia": "Como medimos",
  "vitrine.nav.fontes": "Fontes",
  "vitrine.nav.pular_para_conteudo": "Pular para o conteúdo",
  "vitrine.dados_ilustrativos":
    "Números ilustrativos. Ainda não foram calculados com dados reais.",
  "vitrine.rodape":
    "Projeto independente, sem fins comerciais. Não é recomendação de investimento. Sem vínculo com a SEC, a CVM, a B3, a S&P Dow Jones Indices, os gestores dos ETFs ou as empresas citadas. Nomes de índices, fundos e empresas pertencem aos seus titulares e aparecem só para identificar as carteiras.",

  // Vitrine > Início
  "vitrine.inicio.titulo":
    "Quanto uma carteira depende, de fato, da cadeia de IA?",
  "vitrine.inicio.subtitulo":
    "Abrimos três carteiras públicas até as empresas e medimos quanto cada empresa depende da cadeia de IA.",
  "vitrine.inicio.aviso":
    "Projeto independente, sem fins comerciais. Não é recomendação de investimento.",
  "vitrine.inicio.escolha": "Escolha uma carteira",
  "vitrine.inicio.camadas.titulo": "Do ETF à empresa, em quatro camadas",
  "vitrine.inicio.camadas.carteira":
    "Carteira: partimos dos pesos de cada posição.",
  "vitrine.inicio.camadas.fundos":
    "Fundos: trocamos cada ETF pelas empresas que ele declara ter.",
  "vitrine.inicio.camadas.empresas":
    "Empresas: somamos a mesma empresa quando ela aparece por mais de um caminho.",
  "vitrine.inicio.camadas.exposicao":
    "Exposição: medimos quanto cada empresa depende da cadeia de IA.",

  // Vitrine > Carteiras
  "vitrine.carteira.big_techs.nome": "4 big techs americanas",
  "vitrine.carteira.big_techs.descricao":
    "NVIDIA, Amazon, Apple e Microsoft, 25% cada.",
  "vitrine.carteira.sp500.nome": "S&P 500",
  "vitrine.carteira.sp500.descricao":
    "Um ETF que replica o índice (IVV), aberto pela carteira que ele declara à SEC.",
  "vitrine.carteira.ibovespa.nome": "Ibovespa",
  "vitrine.carteira.ibovespa.descricao":
    "Um ETF que replica o índice (BOVA11), aberto pela carteira que ele informa à CVM.",
  "vitrine.carteira.etf_do_indice":
    "Carteira do {etf}, ETF que replica o índice, em {data}. Não é a composição oficial do índice.",
  "vitrine.carteira.data_referencia": "Carteira de {data}",
  "vitrine.carteira.data_calculo": "Calculado em {data}",

  // Vitrine > Metodologia, fontes e erros
  "vitrine.metodologia.titulo": "Como medimos",
  "vitrine.metodologia.nao_faz":
    "O modelo não prevê preço e não diz o que comprar ou vender. Ele descreve quanto da atividade de cada empresa está ligada à cadeia de IA.",
  "vitrine.metodologia.provisorio":
    "Esta página ainda está sendo escrita. O método completo entra aqui em breve.",
  "vitrine.fontes.titulo": "Fontes e licenças",
  "vitrine.fontes.intro":
    "Todos os números da vitrine vêm de dados públicos. Estas são as fontes e as licenças que seguimos.",
  "vitrine.fontes.cvm":
    "Fonte: CVM, Dados Abertos (licença ODbL). Carteira do BOVA11 pela Composição e Diversificação das Aplicações (CDA).",
  "vitrine.fontes.sec":
    "Fonte: SEC, sistema EDGAR (dados públicos dos Estados Unidos). Carteira do IVV pelo formulário N-PORT.",
  "vitrine.fontes.sem_vinculo":
    "A Sagital não tem vínculo com a CVM, a SEC ou as empresas citadas, nem fala em nome delas.",
  "vitrine.fontes.licenca_cvm": "Licença ODbL",
  "vitrine.carregando": "Carregando os dados da carteira.",
  "vitrine.erro.carregar":
    "Não foi possível carregar esta carteira. Recarregue a página para tentar de novo.",
  "vitrine.erro.formato":
    "Os dados desta carteira estão num formato que o site não reconhece. Tente outra carteira.",
  "vitrine.erro.pagina": "Esta página não existe.",
  "vitrine.erro.voltar": "Voltar às carteiras",
} as const;

export type IdTexto = keyof typeof textos;

// Preenche os trechos entre chaves ({data}, {percentual}...) com os valores da análise.
// Falha se faltar um valor: uma chave crua na tela seria pior que o erro no teste.
export function preencher(
  modelo: string,
  valores: Record<string, string>,
): string {
  return modelo.replace(/\{(\w+)\}/g, (_, chave: string) => {
    const valor = valores[chave];
    if (valor === undefined) {
      throw new Error(`falta o valor de {${chave}}`);
    }
    return valor;
  });
}
