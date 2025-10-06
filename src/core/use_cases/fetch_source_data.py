# src/core/use_cases/fetch_source_data.py
from dataclasses import dataclass

from core.entities.transformation_job import ApiRequest, ApiResponse, TransformationJob
from core.ports.source_port import SourcePort


@dataclass
class FetchSourceDataUseCase:
    """Use case for fetching data from source API."""

    source_adapter: SourcePort  # Dependency injection via port

    async def execute(
        self,
        job: TransformationJob,
        request_config: ApiRequest,
    ) -> ApiResponse:
        """
        Execute the fetch operation.

        Args:
            job: The transformation job being processed
            request_config: Configuration for the API request

        Returns:
            ApiResponse containing the fetched data

        Raises:
            SourceFetchError: If fetching fails
        """
        job.mark_as_fetching()

        try:
            response = await self.source_adapter.fetch(request_config)
            return response
        except Exception as e:
            job.mark_as_failed(f"Failed to fetch source data: {str(e)}")
            raise
