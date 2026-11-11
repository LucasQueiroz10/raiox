import { useSyncExternalStore } from "react";

// Navegação pela History API, sem biblioteca de rotas: são cinco páginas, e cada dependência
// a mais no front entra na cadeia de fornecimento do site (ADR 0009, pendências de segurança).

const EVENTO_NAVEGOU = "vitrine:navegou";

function inscrever(aoMudar: () => void): () => void {
  window.addEventListener("popstate", aoMudar);
  window.addEventListener(EVENTO_NAVEGOU, aoMudar);
  return () => {
    window.removeEventListener("popstate", aoMudar);
    window.removeEventListener(EVENTO_NAVEGOU, aoMudar);
  };
}

function caminhoAtual(): string {
  return window.location.pathname;
}

export function useCaminho(): string {
  return useSyncExternalStore(inscrever, caminhoAtual);
}

export function navegar(caminho: string): void {
  if (caminho === window.location.pathname) return;
  window.history.pushState({}, "", caminho);
  window.dispatchEvent(new Event(EVENTO_NAVEGOU));
}
