import { describe, expect, it } from "vitest";

import { caminhoDaCarteira, resolverRota } from "./rotas";

describe("resolverRota", () => {
  it("reconhece o início", () => {
    expect(resolverRota("/")).toEqual({ nome: "inicio" });
  });

  it("reconhece as três carteiras pelo id da URL", () => {
    expect(resolverRota("/carteira/big-techs")).toEqual({
      nome: "carteira",
      id: "big-techs",
    });
    expect(resolverRota("/carteira/sp500")).toEqual({
      nome: "carteira",
      id: "sp500",
    });
    expect(resolverRota("/carteira/ibovespa")).toEqual({
      nome: "carteira",
      id: "ibovespa",
    });
  });

  it("aceita barra no fim, porque links colados costumam vir assim", () => {
    expect(resolverRota("/carteira/sp500/")).toEqual({
      nome: "carteira",
      id: "sp500",
    });
    expect(resolverRota("/fontes/")).toEqual({ nome: "fontes" });
  });

  it("reconhece as páginas de metodologia e de fontes", () => {
    expect(resolverRota("/metodologia")).toEqual({ nome: "metodologia" });
    expect(resolverRota("/fontes")).toEqual({ nome: "fontes" });
  });

  it("trata carteira desconhecida como página inexistente", () => {
    expect(resolverRota("/carteira/minha-carteira")).toEqual({
      nome: "nao_encontrada",
    });
  });

  it("trata qualquer outro caminho como página inexistente", () => {
    expect(resolverRota("/admin")).toEqual({ nome: "nao_encontrada" });
    expect(resolverRota("/carteira")).toEqual({ nome: "nao_encontrada" });
    expect(resolverRota("/carteira/sp500/extra")).toEqual({
      nome: "nao_encontrada",
    });
  });
});

describe("caminhoDaCarteira", () => {
  it("monta o caminho que resolverRota reconhece", () => {
    expect(resolverRota(caminhoDaCarteira("ibovespa"))).toEqual({
      nome: "carteira",
      id: "ibovespa",
    });
  });
});
