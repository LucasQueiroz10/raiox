import { CARTEIRAS, type IdCarteira } from "../carteiras";
import { Link } from "../componentes/Link";
import { dataDeReferencia, dataDoCalculo } from "../formatar";
import { caminhoDaCarteira } from "../rotas";
import { preencher, textos } from "../textos";
import type { Snapshot } from "../vitrine/snapshots";
import { useSnapshot } from "../vitrine/useSnapshot";

type Props = { id: IdCarteira };

// Raio-x da carteira: seletor, identificação e as datas do snapshot. Os números da exposição
// entram no PR 3.
export function Carteira({ id }: Props) {
  const carteira = CARTEIRAS.find((c) => c.id === id)!;
  const resultado = useSnapshot(id);

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

      {resultado.estado === "carregando" && (
        <p className="aviso" role="status">
          {textos["vitrine.carregando"]}
        </p>
      )}
      {resultado.estado === "erro" && (
        <p className="erro" role="alert">
          {resultado.tipo === "formato"
            ? textos["vitrine.erro.formato"]
            : textos["vitrine.erro.carregar"]}
        </p>
      )}
      {resultado.estado === "pronto" && (
        <DatasDaCarteira snapshot={resultado.snapshot} />
      )}
    </article>
  );
}

// Data de referência e data do cálculo, sempre visíveis (especificação, seção 5.2, item 8).
// Carteira de ETF diz que é a carteira do ETF, não a composição oficial do índice.
function DatasDaCarteira({ snapshot }: { snapshot: Snapshot }) {
  const referencia = dataDeReferencia(snapshot.carteira.data_referencia);
  const [primeira] = snapshot.carteira.posicoes;
  const deEtf =
    snapshot.carteira.posicoes.length === 1 && primeira.tipo === "etf";

  return (
    <div className="datas">
      <p>
        {deEtf
          ? preencher(textos["vitrine.carteira.etf_do_indice"], {
              etf: primeira.ticker,
              data: referencia,
            })
          : preencher(textos["vitrine.carteira.data_referencia"], {
              data: referencia,
            })}
      </p>
      <p>
        {preencher(textos["vitrine.carteira.data_calculo"], {
          data: dataDoCalculo(snapshot.modelo.gerado_em),
        })}
      </p>
    </div>
  );
}
