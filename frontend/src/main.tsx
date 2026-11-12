import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Fontes servidas pelo próprio site (OFL): o navegador não busca nada em outro domínio.
import "@fontsource-variable/schibsted-grotesk";
import "./estilos.css";

import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
