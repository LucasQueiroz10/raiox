import type { ReactNode } from "react";

import { textos } from "../textos";
import { DADOS_ILUSTRATIVOS } from "../vitrine/snapshots";
import { Link } from "./Link";

type Props = { caminho: string; children: ReactNode };

const LINKS_DO_TOPO = [
  { href: "/metodologia", texto: textos["vitrine.nav.metodologia"] },
  { href: "/fontes", texto: textos["vitrine.nav.fontes"] },
];

// Moldura de todas as páginas: atalho para o conteúdo, cabeçalho e o rodapé com os avisos
// obrigatórios (especificação, seção 8).
export function Moldura({ caminho, children }: Props) {
  return (
    <>
      <a className="pular" href="#conteudo">
        {textos["vitrine.nav.pular_para_conteudo"]}
      </a>
      {/* Com dados de exemplo, a faixa aparece em todas as telas (especificação, seção 12). */}
      {DADOS_ILUSTRATIVOS && (
        <p className="faixa-ilustrativa">
          {textos["vitrine.dados_ilustrativos"]}
        </p>
      )}
      <header className="topo">
        <Link
          className="marca"
          href="/"
          aria-current={caminho === "/" ? "page" : undefined}
        >
          <MarcaSagital />
          <span>{textos["vitrine.marca"]}</span>
        </Link>
        <nav className="topo-links">
          {LINKS_DO_TOPO.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              aria-current={caminho === link.href ? "page" : undefined}
            >
              {link.texto}
            </Link>
          ))}
        </nav>
      </header>
      <main id="conteudo" className="conteudo" tabIndex={-1}>
        {children}
      </main>
      <footer className="rodape">
        <p>{textos["vitrine.rodape"]}</p>
      </footer>
    </>
  );
}

// O plano sagital divide o corpo ao meio, de frente para trás: um círculo cortado por uma linha.
function MarcaSagital() {
  return (
    <svg
      className="marca-simbolo"
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="12" cy="12" r="8.25" />
      <line x1="12" y1="1.5" x2="12" y2="22.5" />
    </svg>
  );
}
