# src/core/ports/source_port.py
from typing import Protocol

from core.entities.transformation_job import ApiRequest, ApiResponse


class SourcePort(Protocol):
    """Port for fetching data from source APIs."""

    async def fetch(self, request: ApiRequest) -> ApiResponse:
        """
        Fetch data from source API.

        Args:
            request: API request configuration

        Returns:
            ApiResponse with fetched data

        Raises:
            SourceFetchError: If fetch operation fails
        """
        ...
