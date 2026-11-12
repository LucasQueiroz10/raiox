import { useEffect, useRef } from "react";

import { CARTEIRAS } from "./carteiras";
import { Moldura } from "./componentes/Moldura";
import { useCaminho } from "./navegacao";
import { Carteira } from "./paginas/Carteira";
import { Inicio } from "./paginas/Inicio";
import { Fontes, Metodologia, NaoEncontrada } from "./paginas/Paginas";
import { resolverRota, type Rota } from "./rotas";
import { textos } from "./textos";

function tituloDaPagina(rota: Rota): string | null {
  switch (rota.nome) {
    case "inicio":
      return null;
    case "carteira":
      return textos[CARTEIRAS.find((c) => c.id === rota.id)!.nome];
    case "metodologia":
      return textos["vitrine.metodologia.titulo"];
    case "fontes":
      return textos["vitrine.fontes.titulo"];
    case "nao_encontrada":
      return textos["vitrine.erro.pagina"];
  }
}

function Pagina({ rota }: { rota: Rota }) {
  switch (rota.nome) {
    case "inicio":
      return <Inicio />;
    case "carteira":
      return <Carteira id={rota.id} />;
    case "metodologia":
      return <Metodologia />;
    case "fontes":
      return <Fontes />;
    case "nao_encontrada":
      return <NaoEncontrada />;
  }
}

export default function App() {
  const caminho = useCaminho();
  const rota = resolverRota(caminho);
  const primeiraPagina = useRef(true);

  useEffect(() => {
    const titulo = tituloDaPagina(rota);
    const marca = textos["vitrine.marca"];
    document.title = titulo ? `${titulo} - ${marca}` : marca;

    // Numa troca de página sem recarregar, o leitor de tela não percebe a mudança sozinho:
    // o foco vai para o título da página nova e a rolagem volta ao topo. Na primeira página,
    // o navegador já cuida disso.
    if (primeiraPagina.current) {
      primeiraPagina.current = false;
      return;
    }
    document.documentElement.scrollTop = 0;
    document.querySelector<HTMLElement>("main h1")?.focus();
  }, [caminho]); // eslint-disable-line react-hooks/exhaustive-deps -- a rota deriva do caminho

  return (
    <Moldura caminho={caminho}>
      <Pagina rota={rota} />
    </Moldura>
  );
}
