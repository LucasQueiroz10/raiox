import { Link } from "../componentes/Link";
import { textos } from "../textos";

// Licença da base de dados da CVM, citada junto do crédito (matriz de dados, fonte 1).
const URL_LICENCA_ODBL = "https://opendatacommons.org/licenses/odbl/1-0/";

export function Metodologia() {
  return (
    <article className="leitura">
      <h1 tabIndex={-1}>{textos["vitrine.metodologia.titulo"]}</h1>
      <p className="aviso">{textos["vitrine.metodologia.provisorio"]}</p>
      <p>{textos["vitrine.metodologia.nao_faz"]}</p>
    </article>
  );
}

export function Fontes() {
  return (
    <article className="leitura">
      <h1 tabIndex={-1}>{textos["vitrine.fontes.titulo"]}</h1>
      <p>{textos["vitrine.fontes.intro"]}</p>
      <ul className="fontes">
        <li>
          <p>{textos["vitrine.fontes.cvm"]}</p>
          <a href={URL_LICENCA_ODBL} rel="noreferrer">
            {textos["vitrine.fontes.licenca_cvm"]}
          </a>
        </li>
        <li>
          <p>{textos["vitrine.fontes.sec"]}</p>
        </li>
      </ul>
      <p className="aviso">{textos["vitrine.fontes.sem_vinculo"]}</p>
    </article>
  );
}

export function NaoEncontrada() {
  return (
    <article className="leitura">
      <h1 tabIndex={-1}>{textos["vitrine.erro.pagina"]}</h1>
      <Link className="voltar" href="/">
        {textos["vitrine.erro.voltar"]}
      </Link>
    </article>
  );
}
