import type { AnchorHTMLAttributes, MouseEvent } from "react";

import { navegar } from "../navegacao";

type Props = AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };

// Link interno: troca de página sem recarregar. Clique com Ctrl, Shift, Cmd ou o botão do meio
// segue o comportamento normal do navegador (nova aba, nova janela).
export function Link({ href, onClick, ...resto }: Props) {
  function aoClicar(evento: MouseEvent<HTMLAnchorElement>) {
    onClick?.(evento);
    if (
      evento.defaultPrevented ||
      evento.button !== 0 ||
      evento.metaKey ||
      evento.ctrlKey ||
      evento.shiftKey ||
      evento.altKey
    ) {
      return;
    }
    evento.preventDefault();
    navegar(href);
  }

  return <a href={href} onClick={aoClicar} {...resto} />;
}
