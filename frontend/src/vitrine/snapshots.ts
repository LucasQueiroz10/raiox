import type { IdCarteira } from "../carteiras";
import type { components } from "./tipos";

// Snapshot de uma carteira, com o tipo gerado do modelo do backend (vitrine/snapshot.py).
export type Snapshot = components["schemas"]["Snapshot"];

// Enquanto a V-01 do ADR 0009 não liberar dados reais, o site usa os snapshots de exemplo,
// gerados no backend (python -m vitrine.exemplo), e mostra a faixa "Números ilustrativos".
export const DADOS_ILUSTRATIVOS = true;

// Um arquivo por carteira, carregado só quando a carteira abre.
const CARREGADORES: Record<IdCarteira, () => Promise<{ default: unknown }>> = {
  "big-techs": () => import("../dados_exemplo/big-techs.json"),
  sp500: () => import("../dados_exemplo/sp500.json"),
  ibovespa: () => import("../dados_exemplo/ibovespa.json"),
};

export class ErroDeFormato extends Error {
  constructor(motivo: string) {
    super(`snapshot fora do formato: ${motivo}`);
    this.name = "ErroDeFormato";
  }
}

export async function carregarSnapshot(id: IdCarteira): Promise<Snapshot> {
  const modulo = await CARREGADORES[id]();
  return conferirSnapshot(modulo.default, id);
}

// Checagem leve (ADR 0009, seção 2). O contrato inteiro é garantido no lote e no CI pelo modelo
// Pydantic; validar o JSON Schema no navegador exigiria eval, que a CSP do site proíbe (S-3).
// Aqui só o que pegaria um arquivo trocado ou de outra versão.
export function conferirSnapshot(dado: unknown, id: IdCarteira): Snapshot {
  if (typeof dado !== "object" || dado === null || Array.isArray(dado)) {
    throw new ErroDeFormato("não é um objeto");
  }
  const snapshot = dado as Partial<Snapshot>;
  if (snapshot.versao_schema !== "1") {
    throw new ErroDeFormato("versão do esquema");
  }
  if (snapshot.carteira?.id !== id) {
    throw new ErroDeFormato("arquivo de outra carteira");
  }
  if (snapshot.ilustrativo !== DADOS_ILUSTRATIVOS) {
    throw new ErroDeFormato("marca de dados ilustrativos");
  }
  if (!Array.isArray(snapshot.empresas)) {
    throw new ErroDeFormato("lista de empresas");
  }
  return snapshot as Snapshot;
}

// Os mesmos domínios de vitrine/snapshot.py (DOMINIOS_DE_FONTE). O contrato já recusa no CI;
// esta é a segunda trava, no navegador, antes de um link virar <a href> (S-1 do ADR 0009).
const DOMINIOS_DE_FONTE = [
  "sec.gov",
  "cvm.gov.br",
  "uspto.gov",
  "patentsview.org",
  "openalex.org",
  "ibge.gov.br",
  "gov.br",
  "bcb.gov.br",
  "opendatacommons.org",
];

export function linkSeguro(url: string): string | null {
  let endereco: URL;
  try {
    endereco = new URL(url);
  } catch {
    return null;
  }
  const host = endereco.hostname.toLowerCase();
  const permitido =
    endereco.protocol === "https:" &&
    DOMINIOS_DE_FONTE.some(
      (dominio) => host === dominio || host.endsWith(`.${dominio}`),
    );
  return permitido ? url : null;
}
