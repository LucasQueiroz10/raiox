import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import App from "./App";
import { textos } from "./textos";

function abrirEm(caminho: string) {
  window.history.pushState({}, "", caminho);
  return render(<App />);
}

afterEach(() => {
  window.history.pushState({}, "", "/");
});

describe("App", () => {
  it("renderiza a área principal sem erro", () => {
    render(<App />);

    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("mostra em todas as páginas o rodapé com os avisos", () => {
    for (const caminho of [
      "/",
      "/carteira/sp500",
      "/metodologia",
      "/fontes",
      "/nao-existe",
    ]) {
      const { unmount } = abrirEm(caminho);
      expect(screen.getByRole("contentinfo")).toHaveTextContent(
        textos["vitrine.rodape"],
      );
      unmount();
    }
  });

  it("oferece um atalho para pular direto ao conteúdo", () => {
    abrirEm("/");

    const atalho = screen.getByRole("link", {
      name: textos["vitrine.nav.pular_para_conteudo"],
    });
    expect(atalho).toHaveAttribute("href", "#conteudo");
    expect(screen.getByRole("main")).toHaveAttribute("id", "conteudo");
  });
});

describe("Início", () => {
  it("abre com a pergunta da vitrine e o aviso", () => {
    abrirEm("/");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      textos["vitrine.inicio.titulo"],
    );
    expect(
      screen.getByText(textos["vitrine.inicio.aviso"]),
    ).toBeInTheDocument();
  });

  it("lista as três carteiras com link para o raio-x de cada uma", () => {
    abrirEm("/");

    const lista = screen.getByRole("list", {
      name: textos["vitrine.inicio.escolha"],
    });
    const links = within(lista).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/carteira/big-techs",
      "/carteira/sp500",
      "/carteira/ibovespa",
    ]);
  });

  it("explica as quatro camadas da abertura", () => {
    abrirEm("/");

    const figura = screen.getByRole("figure", {
      name: textos["vitrine.inicio.camadas.titulo"],
    });
    for (const id of [
      "vitrine.inicio.camadas.carteira",
      "vitrine.inicio.camadas.fundos",
      "vitrine.inicio.camadas.empresas",
      "vitrine.inicio.camadas.exposicao",
    ] as const) {
      expect(figura).toHaveTextContent(textos[id]);
    }
  });

  it("não tem campo para o visitante enviar carteira, ticker ou arquivo", () => {
    const { container } = abrirEm("/");

    expect(container.querySelector("input, textarea, select, form")).toBeNull();
  });
});

describe("Navegação", () => {
  it("troca de página sem recarregar ao clicar num link interno", () => {
    abrirEm("/");

    fireEvent.click(screen.getByRole("link", { name: /S&P 500/ }));

    expect(window.location.pathname).toBe("/carteira/sp500");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      textos["vitrine.carteira.sp500.nome"],
    );
  });

  it("atualiza o título da aba com a página atual", () => {
    abrirEm("/fontes");

    expect(document.title).toBe(
      `${textos["vitrine.fontes.titulo"]} - ${textos["vitrine.marca"]}`,
    );
  });

  it("volta para a página anterior pelo botão voltar do navegador", () => {
    abrirEm("/");
    fireEvent.click(
      screen.getByRole("link", { name: textos["vitrine.nav.fontes"] }),
    );

    window.history.pushState({}, "", "/");
    fireEvent.popState(window);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      textos["vitrine.inicio.titulo"],
    );
  });
});

describe("Raio-x da carteira", () => {
  it("mantém o seletor das três carteiras e marca a atual", () => {
    abrirEm("/carteira/ibovespa");

    const seletor = screen.getByRole("navigation", {
      name: textos["vitrine.nav.carteiras"],
    });
    const atual = within(seletor).getByRole("link", { current: "page" });
    expect(atual).toHaveAttribute("href", "/carteira/ibovespa");
    expect(within(seletor).getAllByRole("link")).toHaveLength(3);
  });
});

describe("Fontes", () => {
  it("credita a CVM com link para a licença ODbL e a SEC", () => {
    abrirEm("/fontes");

    expect(screen.getByText(textos["vitrine.fontes.cvm"])).toBeInTheDocument();
    expect(screen.getByText(textos["vitrine.fontes.sec"])).toBeInTheDocument();
    const licenca = screen.getByRole("link", {
      name: textos["vitrine.fontes.licenca_cvm"],
    });
    expect(licenca.getAttribute("href")).toMatch(/^https:\/\//);
  });
});

describe("Página inexistente", () => {
  it("avisa e oferece o caminho de volta às carteiras", () => {
    abrirEm("/admin");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      textos["vitrine.erro.pagina"],
    );
    expect(
      screen.getByRole("link", { name: textos["vitrine.erro.voltar"] }),
    ).toHaveAttribute("href", "/");
  });
});

describe("Dados de exemplo", () => {
  it("mostra a faixa de números ilustrativos em todas as páginas", () => {
    for (const caminho of ["/", "/carteira/sp500", "/fontes", "/nao-existe"]) {
      const { unmount } = abrirEm(caminho);
      expect(
        screen.getByText(textos["vitrine.dados_ilustrativos"]),
      ).toBeInTheDocument();
      unmount();
    }
  });

  it("mostra a data da carteira do ETF depois de carregar", async () => {
    abrirEm("/carteira/sp500");

    expect(
      await screen.findByText(
        "Carteira do IVV, ETF que replica o índice, em 30/09/2026. Não é a composição oficial do índice.",
      ),
    ).toBeInTheDocument();
  });
});
