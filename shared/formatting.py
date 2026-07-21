"""Consistent user-facing formatting for Financial GPS."""

from __future__ import annotations

from datetime import date, datetime


def format_currency(value: float | int | None, *, show_plus: bool = False, decimals: int = 2) -> str:
    amount = float(value or 0)
    sign = "+" if show_plus and amount > 0 else "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.{decimals}f}"


def format_date(value: str | date | datetime | None, *, fallback: str = "Unknown date") -> str:
    if value is None or value == "":
        return fallback
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        try:
            parsed = date.fromisoformat(str(value)[:10])
        except ValueError:
            return str(value)
    return parsed.strftime("%b %d, %Y").replace(" 0", " ")


def format_month(value: str | date | datetime) -> str:
    """Format a month key without letting chart libraries infer daily ticks."""
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        parsed = date.fromisoformat(f"{str(value)[:7]}-01")
    return parsed.strftime("%b %Y")
