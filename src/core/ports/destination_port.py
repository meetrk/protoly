# src/core/ports/destination_port.py
from typing import Any, Protocol

from src.core.entities.transformation_job import ApiRequest


class DestinationPort(Protocol):
    """Port for delivering data to destination endpoints."""

    async def deliver(self, destination: ApiRequest, data: dict[str, Any]) -> None:
        """
        Deliver transformed data via HTTPS POST.

        Args:
            destination: Destination endpoint configuration
            data: Transformed data to deliver

        Raises:
            DeliveryError: If delivery fails
        """
        ...
