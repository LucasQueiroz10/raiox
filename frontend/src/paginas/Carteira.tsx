import { CARTEIRAS, type IdCarteira } from "../carteiras";
import { Link } from "../componentes/Link";
import { caminhoDaCarteira } from "../rotas";
import { textos } from "../textos";

type Props = { id: IdCarteira };

// Esqueleto do raio-x: o seletor e a identificação da carteira. Os números entram com os
// snapshots (PR 2) e as telas de exposição (PR 3).
export function Carteira({ id }: Props) {
  const carteira = CARTEIRAS.find((c) => c.id === id)!;

  return (
    <article className="carteira">
      <nav className="seletor" aria-label={textos["vitrine.nav.carteiras"]}>
        {CARTEIRAS.map((c) => (
          <Link
            key={c.id}
            href={caminhoDaCarteira(c.id)}
            aria-current={c.id === id ? "page" : undefined}
          >
            {textos[c.nome]}
          </Link>
        ))}
      </nav>

      <h1 tabIndex={-1}>{textos[carteira.nome]}</h1>
      <p className="carteira-descricao">{textos[carteira.descricao]}</p>
    </article>
  );
}
