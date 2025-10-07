# src/services/transformation/transformations/uppercase.py
from typing import Any


def transform(value: Any, **params) -> str:
    """Convert string to uppercase."""
    if value is None:
        return ""
    return str(value).upper()
