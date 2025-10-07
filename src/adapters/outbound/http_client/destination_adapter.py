# src/adapters/outbound/http_client/destination_adapter.py
import asyncio
from typing import Any

import httpx

from ....core.entities.transformation_job import ApiRequest
from ....infrastructure.error_handling.exceptions import DeliveryError


class HttpDestinationAdapter:
    """Adapter for delivering data to destination APIs via HTTPS POST."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        """
        Initialize the HTTP destination adapter.

        Args:
            client: Optional pre-configured httpx.AsyncClient
            max_retries: Maximum number of retry attempts
            timeout: Default timeout in seconds
        """
        self._client = client
        self._max_retries = max_retries
        self._default_timeout = timeout
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                timeout=httpx.Timeout(self._default_timeout),
                follow_redirects=True,
            )
        return self._client

    async def deliver(self, destination: ApiRequest, data: dict[str, Any]) -> None:
        """
        Deliver transformed data via HTTPS POST.

        Args:
            destination: Destination endpoint configuration
            data: Transformed data to deliver

        Raises:
            DeliveryError: If delivery fails after retries
        """
        client = await self._get_client()

        for attempt in range(self._max_retries):
            try:
                response = await client.post(
                    url=destination.url,
                    json=data,
                    headers=destination.headers,
                    params=destination.params,
                    timeout=destination.timeout,
                )

                # Check if delivery was successful
                response.raise_for_status()

                # Successful delivery
                return

            except httpx.HTTPStatusError as e:
                if attempt == self._max_retries - 1:
                    raise DeliveryError(
                        f"Failed to deliver data: HTTP {e.response.status_code}",
                    ) from e
                # Exponential backoff
                await asyncio.sleep(2**attempt)

            except httpx.TimeoutException as e:
                if attempt == self._max_retries - 1:
                    raise DeliveryError(f"Delivery timeout: {str(e)}") from e
                await asyncio.sleep(2**attempt)

            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise DeliveryError(f"Unexpected delivery error: {str(e)}") from e
                await asyncio.sleep(2**attempt)

    async def close(self):
        """Close the HTTP client if we own it."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None
