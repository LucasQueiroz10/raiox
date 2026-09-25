"""Calendário de dias úteis: feriados nacionais do calendário ANBIMA."""

from datetime import date


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
