# src/core/use_cases/transform_data.py
from dataclasses import dataclass
from typing import Any

from src.core.entities.transformation_job import TransformationJob
from src.core.ports.transformation_port import TransformationPort


@dataclass
class TransformDataUseCase:
    """Use case for transforming fetched data."""

    transformation_engine: TransformationPort

    async def execute(
        self,
        job: TransformationJob,
        source_data: dict[str, Any],
        transformation_rules: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Execute data transformation.

        Args:
            job: The transformation job being processed
            source_data: Raw data from source API
            transformation_rules: List of transformation rules from config

        Returns:
            Transformed data ready for delivery
        """
        job.mark_as_transforming()

        try:
            transformed_data = await self.transformation_engine.transform(
                source_data,
                transformation_rules,
            )
            return transformed_data
        except Exception as e:
            job.mark_as_failed(f"Failed to transform data: {str(e)}")
            raise
