import { ehIdCarteira, type IdCarteira } from "./carteiras";

// Rotas da vitrine (docs/vitrine/especificacao.md, seção 3). A carteira fica na URL para o
// link poder ser compartilhado. A rota da empresa entra com a tela dela (PR 4).
export type Rota =
  | { nome: "inicio" }
  | { nome: "carteira"; id: IdCarteira }
  | { nome: "metodologia" }
  | { nome: "fontes" }
  | { nome: "nao_encontrada" };

export function resolverRota(caminho: string): Rota {
  // Barra no fim é comum em link colado; "/fontes/" vale o mesmo que "/fontes".
  const partes = caminho.split("/").filter(Boolean);

  if (partes.length === 0) return { nome: "inicio" };
  if (partes.length === 1 && partes[0] === "metodologia")
    return { nome: "metodologia" };
  if (partes.length === 1 && partes[0] === "fontes") return { nome: "fontes" };
  if (
    partes.length === 2 &&
    partes[0] === "carteira" &&
    ehIdCarteira(partes[1])
  ) {
    return { nome: "carteira", id: partes[1] };
  }
  return { nome: "nao_encontrada" };
}

export function caminhoDaCarteira(id: IdCarteira): string {
  return `/carteira/${id}`;
}
