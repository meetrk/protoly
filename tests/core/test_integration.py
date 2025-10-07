# tests/core/test_integration.py
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from src.core.entities.transformation_job import (
    ApiRequest,
    ApiResponse,
    JobStatus,
    TransformationJob,
)
from src.core.use_cases.deliver_data import DeliverDataUseCase
from src.core.use_cases.fetch_source_data import FetchSourceDataUseCase
from src.core.use_cases.transform_data import TransformDataUseCase


# Mock adapters for integration testing
@dataclass
class MockSourceAdapter:
    """Mock source adapter for integration testing."""

    def __init__(self):
        self.fetch = AsyncMock()


@dataclass
class MockTransformationEngine:
    """Mock transformation engine for integration testing."""

    def __init__(self):
        self.transform = AsyncMock()


@dataclass
class MockDestinationAdapter:
    """Mock destination adapter for integration testing."""

    def __init__(self):
        self.deliver = AsyncMock()


class TestCoreIntegration:
    """Test integration of all core use cases."""

    @pytest.fixture()
    def mock_adapters(self):
        """Create mock adapters."""
        return {
            "source": MockSourceAdapter(),
            "transformation": MockTransformationEngine(),
            "destination": MockDestinationAdapter(),
        }

    @pytest.fixture()
    def use_cases(self, mock_adapters):
        """Create use case instances."""
        return {
            "fetch": FetchSourceDataUseCase(source_adapter=mock_adapters["source"]),
            "transform": TransformDataUseCase(
                transformation_engine=mock_adapters["transformation"],
            ),
            "deliver": DeliverDataUseCase(
                destination_adapter=mock_adapters["destination"],
            ),
        }

    @pytest.fixture()
    def sample_api_request(self):
        """Create sample API request."""
        return ApiRequest(
            url="https://api.source.com/users",
            method="GET",
            headers={"Authorization": "Bearer token"},
            timeout=30,
        )

    @pytest.fixture()
    def sample_api_response(self):
        """Create sample API response."""
        return ApiResponse(
            status_code=200,
            data={
                "users": [
                    {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                    },
                    {
                        "id": 2,
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "email": "jane@example.com",
                    },
                ],
            },
            headers={"Content-Type": "application/json"},
            response_time_ms=150.0,
        )

    @pytest.fixture()
    def sample_transformation_rules(self):
        """Create sample transformation rules."""
        return [
            {
                "type": "direct_mapping",
                "source_field": "users[].id",
                "target_field": "customers[].customer_id",
            },
            {
                "type": "concatenate",
                "source_fields": ["users[].first_name", "users[].last_name"],
                "target_field": "customers[].full_name",
                "separator": " ",
            },
        ]

    @pytest.fixture()
    def sample_transformed_data(self):
        """Create sample transformed data."""
        return {
            "customers": [
                {"customer_id": 1, "full_name": "John Doe"},
                {"customer_id": 2, "full_name": "Jane Smith"},
            ],
        }

    @pytest.fixture()
    def sample_destination_config(self):
        """Create sample destination configuration."""
        return ApiRequest(
            url="https://webhook.customer.com/data",
            method="POST",
            headers={"Content-Type": "application/json"},
            timeout=60,
        )

    @pytest.mark.asyncio()
    async def test_complete_pipeline_success(
        self,
        mock_adapters,
        use_cases,
        sample_api_request,
        sample_api_response,
        sample_transformation_rules,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test complete pipeline execution from fetch to delivery."""
        # Setup
        job = TransformationJob(customer_id="test_customer", config_name="test_config")

        # Configure mocks
        mock_adapters["source"].fetch.return_value = sample_api_response
        mock_adapters["transformation"].transform.return_value = sample_transformed_data
        mock_adapters["destination"].deliver.return_value = None

        # Execute complete pipeline

        # Step 1: Fetch data
        api_response = await use_cases["fetch"].execute(job, sample_api_request)
        assert job.status == JobStatus.FETCHING
        assert api_response == sample_api_response

        # Step 2: Transform data
        transformed_data = await use_cases["transform"].execute(
            job,
            api_response.data,
            sample_transformation_rules,
        )
        assert job.status == JobStatus.TRANSFORMING
        assert transformed_data == sample_transformed_data

        # Step 3: Deliver data
        await use_cases["deliver"].execute(
            job,
            transformed_data,
            sample_destination_config,
        )
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None

        # Verify all adapters were called
        mock_adapters["source"].fetch.assert_called_once_with(sample_api_request)
        mock_adapters["transformation"].transform.assert_called_once_with(
            sample_api_response.data,
            sample_transformation_rules,
        )
        mock_adapters["destination"].deliver.assert_called_once_with(
            sample_destination_config,
            sample_transformed_data,
        )

    @pytest.mark.asyncio()
    async def test_pipeline_fails_at_fetch_step(
        self,
        mock_adapters,
        use_cases,
        sample_api_request,
    ):
        """Test pipeline failure at fetch step."""
        # Setup
        job = TransformationJob(customer_id="test_customer", config_name="test_config")
        fetch_error = Exception("Source API unavailable")
        mock_adapters["source"].fetch.side_effect = fetch_error

        # Execute and verify failure
        with pytest.raises(Exception, match="Source API unavailable"):
            await use_cases["fetch"].execute(job, sample_api_request)

        # Verify job is failed and other steps are not executed
        assert job.status == JobStatus.FAILED
        assert job.error_message is not None
        assert "Failed to fetch source data" in job.error_message
        mock_adapters["transformation"].transform.assert_not_called()
        mock_adapters["destination"].deliver.assert_not_called()

    @pytest.mark.asyncio()
    async def test_pipeline_fails_at_transform_step(
        self,
        mock_adapters,
        use_cases,
        sample_api_request,
        sample_api_response,
        sample_transformation_rules,
    ):
        """Test pipeline failure at transform step."""
        # Setup
        job = TransformationJob(customer_id="test_customer", config_name="test_config")
        transform_error = Exception("Invalid transformation rule")
        mock_adapters["source"].fetch.return_value = sample_api_response
        mock_adapters["transformation"].transform.side_effect = transform_error

        # Execute fetch step successfully
        api_response = await use_cases["fetch"].execute(job, sample_api_request)
        assert job.status == JobStatus.FETCHING

        # Execute transform step and verify failure
        with pytest.raises(Exception, match="Invalid transformation rule"):
            await use_cases["transform"].execute(
                job,
                api_response.data,
                sample_transformation_rules,
            )

        # Verify job is failed and delivery step is not executed
        assert job.status == JobStatus.FAILED
        assert job.error_message is not None
        assert "Failed to transform data" in job.error_message
        mock_adapters["destination"].deliver.assert_not_called()

    @pytest.mark.asyncio()
    async def test_pipeline_fails_at_deliver_step(
        self,
        mock_adapters,
        use_cases,
        sample_api_request,
        sample_api_response,
        sample_transformation_rules,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test pipeline failure at delivery step."""
        # Setup
        job = TransformationJob(customer_id="test_customer", config_name="test_config")
        delivery_error = Exception("Webhook endpoint unreachable")
        mock_adapters["source"].fetch.return_value = sample_api_response
        mock_adapters["transformation"].transform.return_value = sample_transformed_data
        mock_adapters["destination"].deliver.side_effect = delivery_error

        # Execute fetch and transform steps successfully
        api_response = await use_cases["fetch"].execute(job, sample_api_request)
        transformed_data = await use_cases["transform"].execute(
            job,
            api_response.data,
            sample_transformation_rules,
        )
        assert job.status == JobStatus.TRANSFORMING

        # Execute delivery step and verify failure
        with pytest.raises(Exception, match="Webhook endpoint unreachable"):
            await use_cases["deliver"].execute(
                job,
                transformed_data,
                sample_destination_config,
            )

        # Verify job is failed
        assert job.status == JobStatus.FAILED
        assert job.error_message is not None
        assert "Failed to deliver data" in job.error_message

    @pytest.mark.asyncio()
    async def test_multiple_concurrent_jobs(
        self,
        mock_adapters,
        use_cases,
        sample_api_request,
        sample_api_response,
        sample_transformation_rules,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test multiple jobs can be processed independently."""
        # Setup
        job1 = TransformationJob(customer_id="customer1", config_name="config1")
        job2 = TransformationJob(customer_id="customer2", config_name="config2")

        # Configure mocks
        mock_adapters["source"].fetch.return_value = sample_api_response
        mock_adapters["transformation"].transform.return_value = sample_transformed_data
        mock_adapters["destination"].deliver.return_value = None

        # Execute complete pipeline for both jobs

        # Job 1
        api_response1 = await use_cases["fetch"].execute(job1, sample_api_request)
        transformed_data1 = await use_cases["transform"].execute(
            job1,
            api_response1.data,
            sample_transformation_rules,
        )
        await use_cases["deliver"].execute(
            job1,
            transformed_data1,
            sample_destination_config,
        )

        # Job 2
        api_response2 = await use_cases["fetch"].execute(job2, sample_api_request)
        transformed_data2 = await use_cases["transform"].execute(
            job2,
            api_response2.data,
            sample_transformation_rules,
        )
        await use_cases["deliver"].execute(
            job2,
            transformed_data2,
            sample_destination_config,
        )

        # Verify both jobs completed successfully
        assert job1.status == JobStatus.COMPLETED
        assert job2.status == JobStatus.COMPLETED
        assert job1.id != job2.id  # Different jobs

        # Verify adapters were called for both jobs
        assert mock_adapters["source"].fetch.call_count == 2
        assert mock_adapters["transformation"].transform.call_count == 2
        assert mock_adapters["destination"].deliver.call_count == 2

    @pytest.mark.asyncio()
    async def test_job_state_consistency_throughout_pipeline(
        self,
        mock_adapters,
        use_cases,
        sample_api_request,
        sample_api_response,
        sample_transformation_rules,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test that job maintains consistent state throughout the pipeline."""
        # Setup
        job = TransformationJob(
            customer_id="consistency_test",
            config_name="consistency_config",
        )
        original_id = job.id
        original_created_at = job.created_at

        # Configure mocks
        mock_adapters["source"].fetch.return_value = sample_api_response
        mock_adapters["transformation"].transform.return_value = sample_transformed_data
        mock_adapters["destination"].deliver.return_value = None

        # Execute complete pipeline
        await use_cases["fetch"].execute(job, sample_api_request)
        await use_cases["transform"].execute(
            job,
            sample_api_response.data,
            sample_transformation_rules,
        )
        await use_cases["deliver"].execute(
            job,
            sample_transformed_data,
            sample_destination_config,
        )

        # Verify job maintains consistent identity and metadata
        assert job.id == original_id
        assert job.customer_id == "consistency_test"
        assert job.config_name == "consistency_config"
        assert job.created_at == original_created_at
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.error_message is None
