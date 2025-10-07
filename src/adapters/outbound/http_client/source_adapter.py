# src/adapters/outbound/http_client/source_adapter.py
import asyncio
import time

import httpx

from ....core.entities.transformation_job import ApiRequest, ApiResponse
from ....infrastructure.error_handling.exceptions import SourceFetchError


class HttpSourceAdapter:
    """Adapter for fetching data from source APIs via HTTP."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        """
        Initialize the HTTP source adapter.

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
        """Get or create HTTP client with connection pooling."""
        if self._client is None:
            # Create client with connection pooling for reuse
            self._client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_connections=100,  # Max total connections
                    max_keepalive_connections=20,  # Keep-alive pool size
                ),
                timeout=httpx.Timeout(self._default_timeout),
                follow_redirects=True,
            )
        return self._client

    async def fetch(self, request: ApiRequest) -> ApiResponse:
        """
        Fetch data from source API.

        Args:
            request: API request configuration

        Returns:
            ApiResponse with fetched data

        Raises:
            SourceFetchError: If fetch operation fails after retries
        """
        client = await self._get_client()

        for attempt in range(self._max_retries):
            try:
                start_time = time.time()

                # Make HTTP request based on method
                response = await self._make_request(client, request)

                response_time_ms = (time.time() - start_time) * 1000

                # Check if response is successful
                response.raise_for_status()

                # Parse response data
                try:
                    data = response.json()
                except Exception:
                    # If not JSON, store as text
                    data = {"raw_content": response.text}

                return ApiResponse(
                    status_code=response.status_code,
                    data=data,
                    headers=dict(response.headers),
                    response_time_ms=response_time_ms,
                )

            except httpx.HTTPStatusError as e:
                if attempt == self._max_retries - 1:
                    raise SourceFetchError(
                        f"HTTP error {e.response.status_code}: {str(e)}",
                    ) from e
                # Exponential backoff
                await asyncio.sleep(2**attempt)

            except httpx.TimeoutException as e:
                if attempt == self._max_retries - 1:
                    raise SourceFetchError(f"Request timeout: {str(e)}") from e
                await asyncio.sleep(2**attempt)

            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise SourceFetchError(f"Unexpected error: {str(e)}") from e
                await asyncio.sleep(2**attempt)

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        request: ApiRequest,
    ) -> httpx.Response:
        """Make HTTP request based on method."""
        method = request.method.upper()

        request_kwargs = {
            "url": request.url,
            "headers": request.headers,
            "params": request.params,
            "timeout": request.timeout,
        }

        if method == "GET":
            return await client.get(**request_kwargs)
        elif method == "POST":
            return await client.post(**request_kwargs, json=request.body)
        elif method == "PUT":
            return await client.put(**request_kwargs, json=request.body)
        elif method == "DELETE":
            return await client.delete(**request_kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    async def close(self):
        """Close the HTTP client if we own it."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None
