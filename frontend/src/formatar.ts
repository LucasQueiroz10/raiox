// Datas em pt-BR, com Intl (frontend/CLAUDE.md).

const DIA_MES_ANO = {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
} as const;

// Data sem hora (AAAA-MM-DD), como a data de referência da carteira. Lida e formatada em UTC:
// new Date("2026-09-30") é meia-noite UTC, e no horário de Brasília viraria 29/09.
const SEM_FUSO = new Intl.DateTimeFormat("pt-BR", {
  ...DIA_MES_ANO,
  timeZone: "UTC",
});

// Momento com hora (o gerado_em do snapshot), mostrado no horário de Brasília.
const BRASILIA = new Intl.DateTimeFormat("pt-BR", {
  ...DIA_MES_ANO,
  timeZone: "America/Sao_Paulo",
});

export function dataDeReferencia(data: string): string {
  return SEM_FUSO.format(new Date(`${data}T00:00:00Z`));
}

export function dataDoCalculo(momento: string): string {
  return BRASILIA.format(new Date(momento));
}
