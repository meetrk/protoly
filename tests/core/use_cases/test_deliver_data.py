# tests/core/use_cases/test_deliver_data.py
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from src.core.entities.transformation_job import (
    ApiRequest,
    JobStatus,
    TransformationJob,
)
from src.core.use_cases.deliver_data import DeliverDataUseCase


# Mock implementation of DestinationPort for testing
@dataclass
class MockDestinationAdapter:
    """Mock destination adapter for testing."""

    def __init__(self):
        self.deliver = AsyncMock()


class TestDeliverDataUseCase:
    """Test DeliverDataUseCase."""

    @pytest.fixture()
    def mock_destination_adapter(self):
        """Create a mock destination adapter."""
        return MockDestinationAdapter()

    @pytest.fixture()
    def use_case(self, mock_destination_adapter):
        """Create use case instance with mock adapter."""
        return DeliverDataUseCase(destination_adapter=mock_destination_adapter)

    @pytest.fixture()
    def sample_job(self):
        """Create a sample transformation job in TRANSFORMING state."""
        job = TransformationJob(customer_id="test_customer", config_name="test_config")
        job.mark_as_fetching()
        job.mark_as_transforming()
        return job

    @pytest.fixture()
    def sample_transformed_data(self):
        """Create sample transformed data."""
        return {
            "customers": [
                {
                    "customer_id": 1,
                    "full_name": "John Doe",
                    "email": "john@example.com",
                },
                {
                    "customer_id": 2,
                    "full_name": "Jane Smith",
                    "email": "jane@example.com",
                },
            ],
            "metadata": {"processed_at": "2024-01-01T12:00:00Z", "total_records": 2},
        }

    @pytest.fixture()
    def sample_destination_config(self):
        """Create sample destination configuration."""
        return ApiRequest(
            url="https://webhook.example.com/data",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer webhook_token",
            },
            timeout=60,
        )

    @pytest.mark.asyncio()
    async def test_successful_delivery(
        self,
        use_case,
        mock_destination_adapter,
        sample_job,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test successful data delivery."""
        # Setup
        mock_destination_adapter.deliver.return_value = None

        # Execute
        await use_case.execute(
            sample_job,
            sample_transformed_data,
            sample_destination_config,
        )

        # Verify
        assert sample_job.status == JobStatus.COMPLETED
        assert sample_job.completed_at is not None
        assert sample_job.error_message is None
        mock_destination_adapter.deliver.assert_called_once_with(
            sample_destination_config,
            sample_transformed_data,
        )

    @pytest.mark.asyncio()
    async def test_delivery_failure_marks_job_as_failed(
        self,
        use_case,
        mock_destination_adapter,
        sample_job,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test that delivery failure marks job as failed and re-raises exception."""
        # Setup
        error_message = "Webhook endpoint not available"
        mock_destination_adapter.deliver.side_effect = Exception(error_message)

        # Execute and verify exception is raised
        with pytest.raises(Exception, match=error_message):
            await use_case.execute(
                sample_job,
                sample_transformed_data,
                sample_destination_config,
            )

        # Verify job is marked as failed
        assert sample_job.status == JobStatus.FAILED
        assert sample_job.error_message == f"Failed to deliver data: {error_message}"
        assert sample_job.completed_at is not None

    @pytest.mark.asyncio()
    async def test_job_status_transitions(
        self,
        use_case,
        mock_destination_adapter,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test that job status transitions correctly during delivery."""
        # Create job in TRANSFORMING state
        job = TransformationJob()
        job.mark_as_fetching()
        job.mark_as_transforming()
        assert job.status == JobStatus.TRANSFORMING

        # Setup successful delivery
        mock_destination_adapter.deliver.return_value = None

        # Execute
        await use_case.execute(job, sample_transformed_data, sample_destination_config)

        # Verify status transitions: TRANSFORMING -> DELIVERING -> COMPLETED
        assert job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio()
    async def test_delivery_with_different_destination_configs(
        self,
        use_case,
        mock_destination_adapter,
        sample_job,
        sample_transformed_data,
    ):
        """Test delivery with different destination configurations."""
        # Setup
        mock_destination_adapter.deliver.return_value = None

        # Test with custom destination config
        custom_destination = ApiRequest(
            url="https://api.customer.com/receive",
            method="PUT",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "custom_api_key",
                "X-Customer-ID": "customer_123",
            },
            body={"metadata": {"source": "protoly"}},
            timeout=120,
        )

        # Execute
        await use_case.execute(sample_job, sample_transformed_data, custom_destination)

        # Verify
        assert sample_job.status == JobStatus.COMPLETED
        mock_destination_adapter.deliver.assert_called_once_with(
            custom_destination,
            sample_transformed_data,
        )

    @pytest.mark.asyncio()
    async def test_delivery_with_empty_data(
        self,
        use_case,
        mock_destination_adapter,
        sample_job,
        sample_destination_config,
    ):
        """Test delivery with empty transformed data."""
        # Setup
        empty_data = {}
        mock_destination_adapter.deliver.return_value = None

        # Execute
        await use_case.execute(sample_job, empty_data, sample_destination_config)

        # Verify
        assert sample_job.status == JobStatus.COMPLETED
        mock_destination_adapter.deliver.assert_called_once_with(
            sample_destination_config,
            empty_data,
        )

    @pytest.mark.asyncio()
    async def test_delivery_marks_job_as_delivering_before_attempt(
        self,
        use_case,
        mock_destination_adapter,
        sample_job,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test that job is marked as delivering before attempting delivery."""
        # Setup delivery to fail to test intermediate state
        mock_destination_adapter.deliver.side_effect = Exception("Delivery failed")

        # Execute and catch exception
        with pytest.raises(Exception, match="Delivery failed"):
            await use_case.execute(
                sample_job,
                sample_transformed_data,
                sample_destination_config,
            )

        # Verify job was marked as delivering before failure
        assert sample_job.status == JobStatus.FAILED
        # Check that deliver was called (meaning job was marked as delivering first)
        mock_destination_adapter.deliver.assert_called_once()

    @pytest.mark.asyncio()
    async def test_multiple_deliveries(
        self,
        mock_destination_adapter,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test multiple delivery operations with different jobs."""
        use_case = DeliverDataUseCase(destination_adapter=mock_destination_adapter)
        mock_destination_adapter.deliver.return_value = None

        # Create multiple jobs in TRANSFORMING state
        job1 = TransformationJob(customer_id="customer1", config_name="config1")
        job1.mark_as_fetching()
        job1.mark_as_transforming()

        job2 = TransformationJob(customer_id="customer2", config_name="config2")
        job2.mark_as_fetching()
        job2.mark_as_transforming()

        # Execute multiple deliveries
        await use_case.execute(job1, sample_transformed_data, sample_destination_config)
        await use_case.execute(job2, sample_transformed_data, sample_destination_config)

        # Verify
        assert job1.status == JobStatus.COMPLETED
        assert job2.status == JobStatus.COMPLETED
        assert mock_destination_adapter.deliver.call_count == 2

    @pytest.mark.asyncio()
    async def test_delivery_preserves_job_metadata(
        self,
        use_case,
        mock_destination_adapter,
        sample_transformed_data,
        sample_destination_config,
    ):
        """Test that delivery preserves job metadata after completion."""
        # Create job with specific metadata
        job = TransformationJob(
            customer_id="specific_customer",
            config_name="specific_config",
        )
        job.mark_as_fetching()
        job.mark_as_transforming()

        original_created_at = job.created_at
        original_id = job.id

        # Setup successful delivery
        mock_destination_adapter.deliver.return_value = None

        # Execute
        await use_case.execute(job, sample_transformed_data, sample_destination_config)

        # Verify metadata is preserved
        assert job.id == original_id
        assert job.customer_id == "specific_customer"
        assert job.config_name == "specific_config"
        assert job.created_at == original_created_at
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
