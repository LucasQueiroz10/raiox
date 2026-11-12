import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // Só nos testes: o textos.test.ts lê docs/textos_telas.md para conferir que cada texto foi
  // copiado literalmente. O servidor de desenvolvimento continua sem acesso fora do frontend/.
  server: mode === "test" ? { fs: { allow: [".", "../docs"] } } : undefined,
  test: {
    environment: "jsdom",
    setupFiles: ["./src/setupTests.ts"],
  },
}));
