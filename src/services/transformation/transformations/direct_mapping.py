# src/services/transformation/transformations/direct_mapping.py
from typing import Any


def transform(value: Any, **params) -> Any:
    """Direct mapping - pass through value unchanged."""
    return value
