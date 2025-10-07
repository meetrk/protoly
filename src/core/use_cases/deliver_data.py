# src/core/use_cases/deliver_data.py
from dataclasses import dataclass
from typing import Any

from src.core.entities.transformation_job import ApiRequest, TransformationJob
from src.core.ports.destination_port import DestinationPort


@dataclass
class DeliverDataUseCase:
    """Use case for delivering transformed data to destination."""

    destination_adapter: DestinationPort

    async def execute(
        self,
        job: TransformationJob,
        transformed_data: dict[str, Any],
        destination_config: ApiRequest,
    ) -> None:
        """
        Execute data delivery via HTTPS POST.

        Args:
            job: The transformation job being processed
            transformed_data: Data to deliver
            destination_config: Destination endpoint configuration
        """
        job.mark_as_delivering()

        try:
            await self.destination_adapter.deliver(destination_config, transformed_data)
            job.mark_as_completed()
        except Exception as e:
            job.mark_as_failed(f"Failed to deliver data: {str(e)}")
            raise
