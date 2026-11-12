import { describe, expect, it } from "vitest";

// O ?raw do Vite traz o arquivo como texto, só no teste; nada disso entra no site.
import textosTelas from "../../docs/textos_telas.md?raw";
import { preencher, textos } from "./textos";

// Linha de tabela do textos_telas.md: | `id` | texto | status |
const LINHA = /^\| `([^`]+)` \| (.*?) \| (rascunho|aprovado|a escrever) \|$/gm;

function textosDoDocumento(): Map<string, { texto: string; status: string }> {
  const mapa = new Map<string, { texto: string; status: string }>();
  for (const [, id, texto, status] of textosTelas.matchAll(LINHA)) {
    mapa.set(id, { texto, status });
  }
  return mapa;
}

describe("textos", () => {
  const documento = textosDoDocumento();

  it("copia cada texto literalmente do docs/textos_telas.md", () => {
    for (const [id, texto] of Object.entries(textos)) {
      expect(documento.get(id)?.texto, id).toBe(texto);
    }
  });

  it("usa só textos da seção da vitrine que já têm texto", () => {
    for (const id of Object.keys(textos)) {
      expect(id.startsWith("vitrine."), id).toBe(true);
      expect(documento.get(id)?.status, id).not.toBe("a escrever");
    }
  });
});

describe("preencher", () => {
  it("troca cada trecho entre chaves pelo valor", () => {
    expect(preencher("Carteira de {data}", { data: "30/09/2026" })).toBe(
      "Carteira de 30/09/2026",
    );
  });

  it("falha quando falta um valor, em vez de mostrar a chave na tela", () => {
    expect(() => preencher("Carteira de {data}", {})).toThrow("data");
  });
});
