import type { IdTexto } from "./textos";

// As três carteiras da vitrine (ADR 0009, seção 2). O id é o que aparece na URL.
// Os números de cada uma chegam pelos snapshots; aqui ficam só a ordem e os textos.
export const CARTEIRAS = [
  {
    id: "big-techs",
    nome: "vitrine.carteira.big_techs.nome",
    descricao: "vitrine.carteira.big_techs.descricao",
  },
  {
    id: "sp500",
    nome: "vitrine.carteira.sp500.nome",
    descricao: "vitrine.carteira.sp500.descricao",
  },
  {
    id: "ibovespa",
    nome: "vitrine.carteira.ibovespa.nome",
    descricao: "vitrine.carteira.ibovespa.descricao",
  },
] as const satisfies readonly {
  id: string;
  nome: IdTexto;
  descricao: IdTexto;
}[];

export type IdCarteira = (typeof CARTEIRAS)[number]["id"];

export function ehIdCarteira(valor: string): valor is IdCarteira {
  return CARTEIRAS.some((carteira) => carteira.id === valor);
}
