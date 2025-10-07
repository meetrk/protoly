# src/services/transformation/transformations/default_value.py
from typing import Any


def transform(value: Any, default: Any = None, **params) -> Any:
    """Return default value if input is None or empty."""
    if value is None or value == "":
        return default
    return value
