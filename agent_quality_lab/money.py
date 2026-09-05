"""Display amounts from integer cents; currency codes use the lab's two-decimal unit."""

from __future__ import annotations

from typing import Any


def format_amount(amount_cents: int, currency: str) -> str:
    whole, fraction = divmod(abs(amount_cents), 100)
    sign = "-" if amount_cents < 0 else ""
    return f"{currency} {sign}{whole}.{fraction:02d}"


def amount_view(value: Any) -> Any:
    """Add a display value to monetary tool records without changing source data."""
    if isinstance(value, list):
        return [amount_view(item) for item in value]
    if isinstance(value, dict):
        result = {key: amount_view(item) for key, item in value.items()}
        if "amount_cents" in value and "currency" in value:
            result["amount_display"] = format_amount(value["amount_cents"], value["currency"])
        return result
    return value
