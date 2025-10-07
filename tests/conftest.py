# tests/conftest.py
"""Shared test fixtures and configuration."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.entities.transformation_job import (
    ApiRequest,
    ApiResponse,
    JobStatus,
    TransformationJob,
)


@pytest.fixture()
def sample_transformation_job():
    """Create a sample transformation job for testing."""
    return TransformationJob(
        id=uuid4(),
        customer_id="test_customer",
        config_name="test_config",
        status=JobStatus.PENDING,
        created_at=datetime.now(tz=UTC),
    )


@pytest.fixture()
def sample_api_request():
    """Create a sample API request for testing."""
    return ApiRequest(
        url="https://api.example.com/data",
        method="GET",
        headers={"Authorization": "Bearer test_token"},
        params={"limit": 100},
        timeout=30,
    )


@pytest.fixture()
def sample_api_response():
    """Create a sample API response for testing."""
    return ApiResponse(
        status_code=200,
        data={
            "users": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
            ],
            "metadata": {"total": 2, "page": 1},
        },
        headers={"Content-Type": "application/json"},
        response_time_ms=150.0,
    )


@pytest.fixture()
def sample_transformation_rules():
    """Create sample transformation rules for testing."""
    return [
        {
            "type": "direct_mapping",
            "source_field": "users[].id",
            "target_field": "customers[].customer_id",
        },
        {
            "type": "direct_mapping",
            "source_field": "users[].name",
            "target_field": "customers[].full_name",
        },
        {
            "type": "direct_mapping",
            "source_field": "users[].email",
            "target_field": "customers[].email_address",
        },
    ]


@pytest.fixture()
def sample_transformed_data():
    """Create sample transformed data for testing."""
    return {
        "customers": [
            {
                "customer_id": 1,
                "full_name": "John Doe",
                "email_address": "john@example.com",
            },
            {
                "customer_id": 2,
                "full_name": "Jane Smith",
                "email_address": "jane@example.com",
            },
        ],
        "metadata": {"processed_count": 2},
    }


@pytest.fixture()
def sample_destination_config():
    """Create a sample destination configuration for testing."""
    return ApiRequest(
        url="https://webhook.example.com/receive",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer webhook_token",
        },
        timeout=60,
    )
