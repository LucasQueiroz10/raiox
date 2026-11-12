import { useId } from "react";

import { CARTEIRAS } from "../carteiras";
import { FiguraCamadas } from "../componentes/FiguraCamadas";
import { Link } from "../componentes/Link";
import { caminhoDaCarteira } from "../rotas";
import { textos } from "../textos";

export function Inicio() {
  const idEscolha = useId();

  return (
    <div className="inicio">
      <div className="inicio-pergunta">
        <h1 tabIndex={-1}>{textos["vitrine.inicio.titulo"]}</h1>
        <p className="inicio-subtitulo">{textos["vitrine.inicio.subtitulo"]}</p>
      </div>

      <div className="inicio-corpo">
        <section aria-labelledby={idEscolha}>
          <p className="aviso">{textos["vitrine.inicio.aviso"]}</p>
          <h2 id={idEscolha} className="inicio-escolha">
            {textos["vitrine.inicio.escolha"]}
          </h2>
          {/* As carteiras são uma lista de séries, como num exame, e não três cartões iguais. */}
          <ul className="series" aria-labelledby={idEscolha}>
            {CARTEIRAS.map((carteira) => (
              <li key={carteira.id}>
                <Link className="serie" href={caminhoDaCarteira(carteira.id)}>
                  <span className="serie-nome">{textos[carteira.nome]}</span>
                  <span className="serie-descricao">
                    {textos[carteira.descricao]}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <FiguraCamadas />
      </div>
    </div>
  );
}
