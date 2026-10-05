import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // src/api/tipos.ts é gerado do OpenAPI (npm run gerar-tipos) e nunca editado à mão.
  { ignores: ["dist", "coverage", "src/api/tipos.ts"] },
  js.configs.recommended,
  tseslint.configs.recommended,
  reactHooks.configs.flat.recommended,
  reactRefresh.configs.vite,
  prettier,
  {
    languageOptions: {
      globals: globals.browser,
    },
  },
);
