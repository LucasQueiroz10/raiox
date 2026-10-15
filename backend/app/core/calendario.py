"""Calendário de dias úteis: feriados nacionais do calendário ANBIMA."""

from datetime import UTC, date, datetime, timedelta, timezone
from functools import cache

# Horário de Brasília. Deslocamento fixo: o Brasil não tem horário de verão desde 2019 (Decreto
# 9.772/2019), e assim não é preciso a base de fusos (tzdata), que o Windows não traz.
BRASILIA = timezone(timedelta(hours=-3), "BRT")

# (mês, dia) dos feriados de data fixa.
_FERIADOS_FIXOS = [(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (12, 25)]


def pascoa(ano: int) -> date:
    """Domingo de Páscoa no calendário gregoriano (algoritmo de Meeus/Jones/Butcher)."""
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    dia_semana = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * dia_semana) // 451
    mes = (h + dia_semana - 7 * m + 114) // 31
    dia = (h + dia_semana - 7 * m + 114) % 31 + 1
    return date(ano, mes, dia)


@cache
def feriados(ano: int) -> frozenset[date]:
    """Feriados nacionais que não são dia útil no calendário ANBIMA."""
    fixos = list(_FERIADOS_FIXOS)
    if ano >= 2024:
        fixos.append((11, 20))  # Consciência Negra, feriado nacional pela Lei 14.759/2023
    p = pascoa(ano)
    moveis = {
        p - timedelta(days=48),  # Carnaval (segunda)
        p - timedelta(days=47),  # Carnaval (terça)
        p - timedelta(days=2),  # Sexta-feira Santa
        p + timedelta(days=60),  # Corpus Christi
    }
    return frozenset({date(ano, mes, dia) for mes, dia in fixos} | moveis)


def dia_util(dia: date) -> bool:
    """Segunda a sexta, fora dos feriados nacionais."""
    return dia.weekday() < 5 and dia not in feriados(dia.year)


def ultimo_dia_util(dia: date) -> date:
    """O próprio dia, se for útil; senão, o dia útil imediatamente anterior."""
    while not dia_util(dia):
        dia -= timedelta(days=1)
    return dia


def hoje_em_brasilia(agora: datetime | None = None) -> date:
    """O dia de hoje em Brasília. O servidor roda em UTC: das 21h à meia-noite de Brasília, o dia
    dele já é o seguinte, e a PTAX pedida sairia com a data errada."""
    return (agora or datetime.now(UTC)).astimezone(BRASILIA).date()
