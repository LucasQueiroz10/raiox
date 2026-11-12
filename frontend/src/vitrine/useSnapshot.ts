import { useEffect, useState } from "react";

import type { IdCarteira } from "../carteiras";
import { ErroDeFormato, carregarSnapshot, type Snapshot } from "./snapshots";

export type EstadoDoSnapshot =
  | { estado: "carregando" }
  | { estado: "pronto"; snapshot: Snapshot }
  | { estado: "erro"; tipo: "carregar" | "formato" };

// Carrega o snapshot da carteira e volta a "carregando" quando a carteira muda.
export function useSnapshot(id: IdCarteira): EstadoDoSnapshot {
  const [resultado, setResultado] = useState<{
    id: IdCarteira;
    estado: EstadoDoSnapshot;
  } | null>(null);

  useEffect(() => {
    let valido = true;
    carregarSnapshot(id).then(
      (snapshot) => {
        if (valido)
          setResultado({ id, estado: { estado: "pronto", snapshot } });
      },
      (erro: unknown) => {
        if (!valido) return;
        const tipo = erro instanceof ErroDeFormato ? "formato" : "carregar";
        setResultado({ id, estado: { estado: "erro", tipo } });
      },
    );
    // Troca de carteira antes de terminar: o resultado antigo é descartado.
    return () => {
      valido = false;
    };
  }, [id]);

  return resultado?.id === id ? resultado.estado : { estado: "carregando" };
}
