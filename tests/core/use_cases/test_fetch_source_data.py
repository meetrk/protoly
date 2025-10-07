# tests/core/use_cases/test_fetch_source_data.py
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from src.core.entities.transformation_job import (
    ApiRequest,
    ApiResponse,
    JobStatus,
    TransformationJob,
)
from src.core.use_cases.fetch_source_data import FetchSourceDataUseCase


# Mock implementation of SourcePort for testing
@dataclass
class MockSourceAdapter:
    """Mock source adapter for testing."""

    def __init__(self):
        self.fetch = AsyncMock()


class TestFetchSourceDataUseCase:
    """Test FetchSourceDataUseCase."""

    @pytest.fixture()
    def mock_source_adapter(self):
        """Create a mock source adapter."""
        return MockSourceAdapter()

    @pytest.fixture()
    def use_case(self, mock_source_adapter):
        """Create use case instance with mock adapter."""
        return FetchSourceDataUseCase(source_adapter=mock_source_adapter)

    @pytest.fixture()
    def sample_job(self):
        """Create a sample transformation job."""
        return TransformationJob(customer_id="test_customer", config_name="test_config")

    @pytest.fixture()
    def sample_request_config(self):
        """Create a sample API request configuration."""
        return ApiRequest(
            url="https://api.example.com/data",
            method="GET",
            headers={"Authorization": "Bearer token"},
            timeout=30,
        )

    @pytest.fixture()
    def sample_api_response(self):
        """Create a sample API response."""
        return ApiResponse(
            status_code=200,
            data={"users": [{"id": 1, "name": "John"}]},
            headers={"Content-Type": "application/json"},
            response_time_ms=150.5,
        )

    @pytest.mark.asyncio()
    async def test_successful_fetch(
        self,
        use_case,
        mock_source_adapter,
        sample_job,
        sample_request_config,
        sample_api_response,
    ):
        """Test successful data fetching."""
        # Setup
        mock_source_adapter.fetch.return_value = sample_api_response

        # Execute
        result = await use_case.execute(sample_job, sample_request_config)

        # Verify
        assert result == sample_api_response
        assert sample_job.status == JobStatus.FETCHING
        mock_source_adapter.fetch.assert_called_once_with(sample_request_config)

    @pytest.mark.asyncio()
    async def test_fetch_failure_marks_job_as_failed(
        self,
        use_case,
        mock_source_adapter,
        sample_job,
        sample_request_config,
    ):
        """Test that fetch failure marks job as failed and re-raises exception."""
        # Setup
        error_message = "Connection timeout"
        mock_source_adapter.fetch.side_effect = Exception(error_message)

        # Execute and verify exception is raised
        with pytest.raises(Exception, match=error_message):
            await use_case.execute(sample_job, sample_request_config)

        # Verify job is marked as failed
        assert sample_job.status == JobStatus.FAILED
        assert (
            sample_job.error_message == f"Failed to fetch source data: {error_message}"
        )
        assert sample_job.completed_at is not None

    @pytest.mark.asyncio()
    async def test_job_status_transition(
        self,
        use_case,
        mock_source_adapter,
        sample_request_config,
        sample_api_response,
    ):
        """Test that job status transitions correctly during fetch."""
        # Create job with PENDING status
        job = TransformationJob()
        assert job.status == JobStatus.PENDING

        # Setup successful response
        mock_source_adapter.fetch.return_value = sample_api_response

        # Execute
        await use_case.execute(job, sample_request_config)

        # Verify status changed to FETCHING
        assert job.status == JobStatus.FETCHING

    @pytest.mark.asyncio()
    async def test_fetch_with_different_request_configs(
        self,
        use_case,
        mock_source_adapter,
        sample_job,
        sample_api_response,
    ):
        """Test fetch with different request configurations."""
        # Setup
        mock_source_adapter.fetch.return_value = sample_api_response

        # Test with POST request
        post_request = ApiRequest(
            url="https://api.example.com/submit",
            method="POST",
            headers={"Content-Type": "application/json"},
            body={"query": "test"},
            timeout=60,
        )

        # Execute
        result = await use_case.execute(sample_job, post_request)

        # Verify
        assert result == sample_api_response
        mock_source_adapter.fetch.assert_called_once_with(post_request)

    @pytest.mark.asyncio()
    async def test_multiple_fetch_attempts(
        self,
        mock_source_adapter,
        sample_request_config,
        sample_api_response,
    ):
        """Test multiple fetch attempts with different jobs."""
        use_case = FetchSourceDataUseCase(source_adapter=mock_source_adapter)
        mock_source_adapter.fetch.return_value = sample_api_response

        # Create multiple jobs
        job1 = TransformationJob(customer_id="customer1", config_name="config1")
        job2 = TransformationJob(customer_id="customer2", config_name="config2")

        # Execute multiple fetches
        result1 = await use_case.execute(job1, sample_request_config)
        result2 = await use_case.execute(job2, sample_request_config)

        # Verify
        assert result1 == sample_api_response
        assert result2 == sample_api_response
        assert job1.status == JobStatus.FETCHING
        assert job2.status == JobStatus.FETCHING
        assert mock_source_adapter.fetch.call_count == 2
