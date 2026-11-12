import { describe, expect, it } from "vitest";

import exemplo from "../dados_exemplo/sp500.json";
import {
  ErroDeFormato,
  carregarSnapshot,
  conferirSnapshot,
  linkSeguro,
} from "./snapshots";

function copia(): Record<string, unknown> {
  return structuredClone(exemplo) as Record<string, unknown>;
}

describe("conferirSnapshot", () => {
  it("aceita o snapshot de exemplo da carteira pedida", () => {
    expect(conferirSnapshot(copia(), "sp500").carteira.id).toBe("sp500");
  });

  it("recusa outra versão do esquema", () => {
    const dado = { ...copia(), versao_schema: "2" };
    expect(() => conferirSnapshot(dado, "sp500")).toThrow(ErroDeFormato);
  });

  it("recusa o snapshot de outra carteira", () => {
    expect(() => conferirSnapshot(copia(), "ibovespa")).toThrow(ErroDeFormato);
  });

  it("recusa dado de exemplo que não esteja marcado como ilustrativo", () => {
    // Com dados de exemplo, a faixa "Números ilustrativos" aparece em todas as telas.
    const dado = { ...copia(), ilustrativo: false };
    expect(() => conferirSnapshot(dado, "sp500")).toThrow(ErroDeFormato);
  });

  it("recusa o que nem é um objeto", () => {
    expect(() => conferirSnapshot(null, "sp500")).toThrow(ErroDeFormato);
    expect(() => conferirSnapshot([], "sp500")).toThrow(ErroDeFormato);
  });
});

describe("carregarSnapshot", () => {
  it("carrega as três carteiras de exemplo", async () => {
    for (const id of ["big-techs", "sp500", "ibovespa"] as const) {
      const snapshot = await carregarSnapshot(id);
      expect(snapshot.carteira.id).toBe(id);
    }
  });
});

describe("linkSeguro", () => {
  // S-1 do ADR 0009: o contrato já recusa no CI; aqui é a segunda trava, no navegador.
  it("aceita https de fonte permitida, inclusive subdomínio", () => {
    expect(linkSeguro("https://www.sec.gov/edgar")).toBe(
      "https://www.sec.gov/edgar",
    );
    expect(linkSeguro("https://dados.cvm.gov.br/")).toBe(
      "https://dados.cvm.gov.br/",
    );
  });

  it("recusa outro esquema, outro domínio e domínio disfarçado", () => {
    expect(linkSeguro("javascript:alert(1)")).toBeNull();
    expect(linkSeguro("http://www.sec.gov/")).toBeNull();
    expect(linkSeguro("https://exemplo.com/")).toBeNull();
    expect(linkSeguro("https://sec.gov.exemplo.com/")).toBeNull();
    expect(linkSeguro("não é url")).toBeNull();
  });
});
