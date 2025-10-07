# tests/core/entities/test_transformation_job.py
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.entities.transformation_job import (
    ApiRequest,
    ApiResponse,
    JobStatus,
    TransformationJob,
)


class TestJobStatus:
    """Test JobStatus enum."""

    def test_job_status_values(self):
        """Test that all job status values are correctly defined."""
        assert JobStatus.PENDING.value == "PENDING"
        assert JobStatus.FETCHING.value == "FETCHING"
        assert JobStatus.TRANSFORMING.value == "TRANSFORMING"
        assert JobStatus.DELIVERING.value == "DELIVERING"
        assert JobStatus.COMPLETED.value == "COMPLETED"
        assert JobStatus.FAILED.value == "FAILED"


class TestTransformationJob:
    """Test TransformationJob entity."""

    def test_transformation_job_creation_with_defaults(self):
        """Test creating a transformation job with default values."""
        job = TransformationJob()

        assert job.id is not None
        assert isinstance(job.id, type(uuid4()))
        assert job.customer_id == ""
        assert job.config_name == ""
        assert job.status == JobStatus.PENDING
        assert isinstance(job.created_at, datetime)
        assert job.completed_at is None
        assert job.error_message is None

    def test_transformation_job_creation_with_custom_values(self):
        """Test creating a transformation job with custom values."""
        custom_id = uuid4()
        custom_time = datetime.now(tz=UTC)

        job = TransformationJob(
            id=custom_id,
            customer_id="customer_123",
            config_name="test_config",
            status=JobStatus.FETCHING,
            created_at=custom_time,
        )

        assert job.id == custom_id
        assert job.customer_id == "customer_123"
        assert job.config_name == "test_config"
        assert job.status == JobStatus.FETCHING
        assert job.created_at == custom_time

    def test_mark_as_fetching_from_pending(self):
        """Test successful transition from PENDING to FETCHING."""
        job = TransformationJob()
        job.mark_as_fetching()

        assert job.status == JobStatus.FETCHING

    def test_mark_as_fetching_from_invalid_status(self):
        """Test that marking as fetching from non-pending status raises error."""
        job = TransformationJob(status=JobStatus.TRANSFORMING)

        with pytest.raises(ValueError, match="Cannot fetch from status"):
            job.mark_as_fetching()

    def test_mark_as_transforming_from_fetching(self):
        """Test successful transition from FETCHING to TRANSFORMING."""
        job = TransformationJob(status=JobStatus.FETCHING)
        job.mark_as_transforming()

        assert job.status == JobStatus.TRANSFORMING

    def test_mark_as_transforming_from_invalid_status(self):
        """Test that marking as transforming from non-fetching status raises error."""
        job = TransformationJob(status=JobStatus.PENDING)

        with pytest.raises(ValueError, match="Cannot transform from status"):
            job.mark_as_transforming()

    def test_mark_as_delivering_from_transforming(self):
        """Test successful transition from TRANSFORMING to DELIVERING."""
        job = TransformationJob(status=JobStatus.TRANSFORMING)
        job.mark_as_delivering()

        assert job.status == JobStatus.DELIVERING

    def test_mark_as_delivering_from_invalid_status(self):
        """Test that marking as delivering from non-transforming status raises error."""
        job = TransformationJob(status=JobStatus.FETCHING)

        with pytest.raises(ValueError, match="Cannot deliver from status"):
            job.mark_as_delivering()

    def test_mark_as_completed(self):
        """Test marking job as completed."""
        job = TransformationJob()
        before_completion = datetime.now(tz=UTC)

        job.mark_as_completed()

        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.completed_at >= before_completion
        assert job.error_message is None

    def test_mark_as_failed(self):
        """Test marking job as failed with error message."""
        job = TransformationJob()
        error_msg = "Something went wrong"
        before_failure = datetime.now(tz=UTC)

        job.mark_as_failed(error_msg)

        assert job.status == JobStatus.FAILED
        assert job.error_message == error_msg
        assert job.completed_at is not None
        assert job.completed_at >= before_failure

    def test_complete_job_workflow(self):
        """Test a complete job workflow through all states."""
        job = TransformationJob(customer_id="test_customer", config_name="test_config")

        # Start with PENDING
        assert job.status == JobStatus.PENDING

        # Move to FETCHING
        job.mark_as_fetching()
        assert job.status == JobStatus.FETCHING

        # Move to TRANSFORMING
        job.mark_as_transforming()
        assert job.status == JobStatus.TRANSFORMING

        # Move to DELIVERING
        job.mark_as_delivering()
        assert job.status == JobStatus.DELIVERING

        # Complete
        job.mark_as_completed()
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None


class TestApiRequest:
    """Test ApiRequest entity."""

    def test_api_request_creation_with_defaults(self):
        """Test creating an API request with default values."""
        request = ApiRequest(url="https://api.example.com/data")

        assert request.url == "https://api.example.com/data"
        assert request.method == "GET"
        assert request.headers == {}
        assert request.params == {}
        assert request.body is None
        assert request.timeout == 30

    def test_api_request_creation_with_custom_values(self):
        """Test creating an API request with custom values."""
        custom_headers = {"Authorization": "Bearer token"}
        custom_params = {"limit": 100}
        custom_body = {"query": "test"}

        request = ApiRequest(
            url="https://api.example.com/search",
            method="POST",
            headers=custom_headers,
            params=custom_params,
            body=custom_body,
            timeout=60,
        )

        assert request.url == "https://api.example.com/search"
        assert request.method == "POST"
        assert request.headers == custom_headers
        assert request.params == custom_params
        assert request.body == custom_body
        assert request.timeout == 60

    def test_api_request_immutable_headers_and_params(self):
        """Test that modifying headers/params after creation works correctly."""
        request = ApiRequest(url="https://api.example.com")

        # Modify headers
        request.headers["X-Custom"] = "value"
        assert request.headers["X-Custom"] == "value"

        # Modify params
        request.params["page"] = 1
        assert request.params["page"] == 1


class TestApiResponse:
    """Test ApiResponse entity."""

    def test_api_response_creation(self):
        """Test creating an API response."""
        response_data = {"users": [{"id": 1, "name": "John"}]}
        response_headers = {"Content-Type": "application/json"}

        response = ApiResponse(
            status_code=200,
            data=response_data,
            headers=response_headers,
            response_time_ms=150.5,
        )

        assert response.status_code == 200
        assert response.data == response_data
        assert response.headers == response_headers
        assert response.response_time_ms == 150.5

    def test_api_response_with_error_status(self):
        """Test creating an API response with error status."""
        error_data = {"error": "Not found"}

        response = ApiResponse(
            status_code=404,
            data=error_data,
            headers={},
            response_time_ms=50.0,
        )

        assert response.status_code == 404
        assert response.data == error_data
