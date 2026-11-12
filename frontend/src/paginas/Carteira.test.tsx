import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { textos } from "../textos";
import { Carteira } from "./Carteira";

const carregar = vi.hoisted(() => vi.fn());

vi.mock("../vitrine/snapshots", async (original) => ({
  ...(await original<typeof import("../vitrine/snapshots")>()),
  carregarSnapshot: carregar,
}));

afterEach(() => {
  carregar.mockReset();
});

describe("Carteira: estados do carregamento", () => {
  it("avisa enquanto carrega", () => {
    carregar.mockReturnValue(new Promise(() => {}));
    render(<Carteira id="sp500" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      textos["vitrine.carregando"],
    );
  });

  it("explica o erro de formato sem quebrar a tela", async () => {
    const { ErroDeFormato } = await import("../vitrine/snapshots");
    carregar.mockRejectedValue(new ErroDeFormato("versão"));
    render(<Carteira id="sp500" />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      textos["vitrine.erro.formato"],
    );
  });

  it("explica a falha de carregamento sem quebrar a tela", async () => {
    carregar.mockRejectedValue(new Error("rede"));
    render(<Carteira id="sp500" />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      textos["vitrine.erro.carregar"],
    );
  });
});
