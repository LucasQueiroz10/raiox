import { useEffect, useId, useRef, useState, type CSSProperties } from "react";

import { textos, type IdTexto } from "../textos";

// Figura de assinatura da vitrine: a carteira como uma pilha de cortes, como num exame de
// imagem. Cada corte é uma camada do look-through. Não há números aqui: os desenhos mostram a
// forma de cada camada (uma posição, poucos fundos, muitas empresas), não dados de carteira.

const COLUNAS = 16;
const LINHAS = 10;

type Camada = { texto: IdTexto; celulas: Celula[] };
type Celula = { x: number; y: number; l: number; a: number; opacidade: number };

// Intensidade determinística por célula, só para o desenho da exposição variar de célula a
// célula. É ilustração, não dado.
function intensidade(i: number): number {
  const v = Math.sin(i * 12.9898) * 43758.5453;
  return 0.18 + (v - Math.floor(v)) * 0.82;
}

function grade(
  colunas: number,
  linhas: number,
  comIntensidade: boolean,
): Celula[] {
  const largura = 240 / colunas;
  const altura = 150 / linhas;
  const celulas: Celula[] = [];
  for (let y = 0; y < linhas; y++) {
    for (let x = 0; x < colunas; x++) {
      celulas.push({
        x: x * largura + 1.5,
        y: y * altura + 1.5,
        l: largura - 3,
        a: altura - 3,
        opacidade: comIntensidade ? intensidade(y * colunas + x) : 1,
      });
    }
  }
  return celulas;
}

const CAMADAS: Camada[] = [
  { texto: "vitrine.inicio.camadas.carteira", celulas: grade(1, 1, false) },
  { texto: "vitrine.inicio.camadas.fundos", celulas: grade(6, 4, false) },
  {
    texto: "vitrine.inicio.camadas.empresas",
    celulas: grade(COLUNAS, LINHAS, false),
  },
  {
    texto: "vitrine.inicio.camadas.exposicao",
    celulas: grade(COLUNAS, LINHAS, true),
  },
];

// A pilha começa fechada e se abre uma vez, quando entra na tela. Sem IntersectionObserver
// (navegador antigo, teste) ou com movimento reduzido, ela já aparece aberta.
function useAbertaAoAparecer() {
  const ref = useRef<HTMLElement>(null);
  const [aberta, setAberta] = useState(false);

  useEffect(() => {
    const elemento = ref.current;
    const reduzido =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    if (!elemento || reduzido || typeof IntersectionObserver === "undefined") {
      setAberta(true);
      return;
    }
    const observador = new IntersectionObserver(
      (entradas) => {
        if (entradas.some((entrada) => entrada.isIntersecting)) {
          setAberta(true);
          observador.disconnect();
        }
      },
      { threshold: 0.35 },
    );
    observador.observe(elemento);
    return () => observador.disconnect();
  }, []);

  return { ref, aberta };
}

export function FiguraCamadas() {
  const idTitulo = useId();
  const { ref, aberta } = useAbertaAoAparecer();

  return (
    <figure
      ref={ref}
      className="camadas"
      data-aberta={aberta}
      aria-labelledby={idTitulo}
    >
      <figcaption id={idTitulo} className="camadas-titulo">
        {textos["vitrine.inicio.camadas.titulo"]}
      </figcaption>
      <ol className="camadas-pilha">
        {CAMADAS.map((camada, indice) => {
          const [nome, ...resto] = textos[camada.texto].split(":");
          return (
            <li
              key={camada.texto}
              className="corte"
              style={{ "--i": indice } as CSSProperties}
            >
              <div className="corte-plano" aria-hidden="true">
                <svg viewBox="0 0 240 150" focusable="false">
                  <rect
                    className="corte-borda"
                    x="0.5"
                    y="0.5"
                    width="239"
                    height="149"
                  />
                  {camada.celulas.map((c, i) => (
                    <rect
                      key={i}
                      className="corte-celula"
                      x={c.x}
                      y={c.y}
                      width={c.l}
                      height={c.a}
                      opacity={c.opacidade}
                    />
                  ))}
                </svg>
              </div>
              <p className="corte-legenda">
                <strong>{nome}:</strong>
                {resto.join(":")}
              </p>
            </li>
          );
        })}
      </ol>
    </figure>
  );
}
