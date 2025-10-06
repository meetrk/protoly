from typing import Any, Protocol


class TransformationPort(Protocol):
    """Port for data transformation operations."""

    async def transform(
        self,
        source_data: dict[str, Any],
        rules: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Transform data according to rules.

        Args:
            source_data: Raw input data
            rules: Transformation rules from config

        Returns:
            Transformed data

        Raises:
            TransformationError: If transformation fails
        """
        ...
