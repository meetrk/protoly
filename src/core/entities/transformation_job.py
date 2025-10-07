# src/core/entities/transformation_job.py
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class JobStatus(Enum):
    PENDING = "PENDING"
    FETCHING = "FETCHING"
    TRANSFORMING = "TRANSFORMING"
    DELIVERING = "DELIVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class TransformationJob:
    """Core entity representing a data transformation job."""

    id: UUID = field(default_factory=uuid4)
    customer_id: str = field(default="")
    config_name: str = field(default="")
    status: JobStatus = field(default=JobStatus.PENDING)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    completed_at: datetime | None = None
    error_message: str | None = None

    def mark_as_fetching(self) -> None:
        """Transition job to fetching state."""
        if self.status != JobStatus.PENDING:
            raise ValueError(f"Cannot fetch from status {self.status}")
        self.status = JobStatus.FETCHING

    def mark_as_transforming(self) -> None:
        """Transition job to transforming state."""
        if self.status != JobStatus.FETCHING:
            raise ValueError(f"Cannot transform from status {self.status}")
        self.status = JobStatus.TRANSFORMING

    def mark_as_delivering(self) -> None:
        """Transition job to delivering state."""
        if self.status != JobStatus.TRANSFORMING:
            raise ValueError(f"Cannot deliver from status {self.status}")
        self.status = JobStatus.DELIVERING

    def mark_as_completed(self) -> None:
        """Mark job as successfully completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(tz=UTC)

    def mark_as_failed(self, error_message: str) -> None:
        """Mark job as failed with error message."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(tz=UTC)


@dataclass
class ApiRequest:
    """Entity representing an API request configuration."""

    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    body: dict[str, Any] | None = None
    timeout: int = 30


@dataclass
class ApiResponse:
    """Entity representing an API response."""

    status_code: int
    data: dict[str, Any]
    headers: dict[str, str]
    response_time_ms: float
