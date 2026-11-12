import { describe, expect, it } from "vitest";

import { dataDoCalculo, dataDeReferencia } from "./formatar";

describe("dataDeReferencia", () => {
  it("formata a data em pt-BR sem voltar um dia pelo fuso", () => {
    // new Date("2026-09-30") seria meia-noite UTC: 29/09 no horário de Brasília.
    expect(dataDeReferencia("2026-09-30")).toBe("30/09/2026");
  });
});

describe("dataDoCalculo", () => {
  it("mostra a data no horário de Brasília", () => {
    expect(dataDoCalculo("2026-11-11T12:00:00Z")).toBe("11/11/2026");
    // Meia-noite UTC ainda é o dia anterior em Brasília.
    expect(dataDoCalculo("2026-11-11T00:00:00Z")).toBe("10/11/2026");
  });
});
