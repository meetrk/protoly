# src/adapters/outbound/transformation/transformation_adapter.py
from collections.abc import Callable
from typing import Any

from ....infrastructure.error_handling.exceptions import TransformationError


class TransformationEngine:
    """Adapter implementing transformation logic."""

    def __init__(self):
        """Initialize transformation engine with registry."""
        self._transformation_registry: dict[str, Callable] = {}
        self._register_builtin_transformations()

    def _register_builtin_transformations(self):
        """Register built-in transformation functions."""
        from ....services.transformation.transformations import (
            concatenate,
            default_value,
            direct_mapping,
            format_date,
            lowercase,
            uppercase,
        )

        self._transformation_registry.update(
            {
                "direct": direct_mapping.transform,
                "format_date": format_date.transform,
                "concatenate": concatenate.transform,
                "uppercase": uppercase.transform,
                "lowercase": lowercase.transform,
                "default_value": default_value.transform,
            },
        )

    def register_transformation(self, name: str, func: Callable):
        """Register a custom transformation function."""
        self._transformation_registry[name] = func

    async def transform(
        self,
        source_data: dict[str, Any],
        rules: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Transform data according to rules.

        Args:
            source_data: Raw input data
            rules: List of transformation rules

        Returns:
            Transformed data

        Raises:
            TransformationError: If transformation fails
        """
        transformed_data = {}

        try:
            for rule in rules:
                target_field = rule.get("target_field")
                source_field = rule.get("source_field")
                transform_type = rule.get("transform", "direct")
                transform_params = rule.get("params", {})

                if not target_field:
                    raise TransformationError("Missing target_field in rule")

                # Get transformation function
                transform_func = self._transformation_registry.get(transform_type)
                if not transform_func:
                    raise TransformationError(
                        f"Unknown transformation type: {transform_type}",
                    )

                # Apply transformation
                try:
                    value = self._extract_value(source_data, source_field)
                    transformed_value = transform_func(value, **transform_params)
                    transformed_data[target_field] = transformed_value
                except Exception as e:
                    raise TransformationError(
                        f"Failed to transform field {target_field}: {str(e)}",
                    ) from e

            return transformed_data

        except Exception as e:
            raise TransformationError(f"Transformation failed: {str(e)}") from e

    def _extract_value(self, data: dict[str, Any], field_path: str) -> Any:
        """Extract value from nested dictionary using dot notation."""
        if not field_path:
            return data

        keys = field_path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value
