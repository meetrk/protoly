# src/services/transformation/transformations/concatenate.py
from typing import Any


def transform(
    value: Any,
    fields: list[str] = None,
    separator: str = " ",
    **params,
) -> str:
    """Concatenate multiple fields."""
    if fields and isinstance(value, dict):
        values = [str(value.get(f, "")) for f in fields]
        return separator.join(values)
    return str(value)
