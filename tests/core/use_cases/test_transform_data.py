# tests/core/use_cases/test_transform_data.py
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from src.core.entities.transformation_job import JobStatus, TransformationJob
from src.core.use_cases.transform_data import TransformDataUseCase


# Mock implementation of TransformationPort for testing
@dataclass
class MockTransformationEngine:
    """Mock transformation engine for testing."""

    def __init__(self):
        self.transform = AsyncMock()


class TestTransformDataUseCase:
    """Test TransformDataUseCase."""

    @pytest.fixture()
    def mock_transformation_engine(self):
        """Create a mock transformation engine."""
        return MockTransformationEngine()

    @pytest.fixture()
    def use_case(self, mock_transformation_engine):
        """Create use case instance with mock engine."""
        return TransformDataUseCase(transformation_engine=mock_transformation_engine)

    @pytest.fixture()
    def sample_job(self):
        """Create a sample transformation job in FETCHING state."""
        job = TransformationJob(customer_id="test_customer", config_name="test_config")
        job.mark_as_fetching()  # Move to fetching state
        return job

    @pytest.fixture()
    def sample_source_data(self):
        """Create sample source data."""
        return {
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
            "metadata": {"total": 2, "page": 1},
        }

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
            {
                "type": "direct_mapping",
                "source_field": "users[].email",
                "target_field": "customers[].email_address",
            },
        ]

    @pytest.fixture()
    def sample_transformed_data(self):
        """Create sample transformed data."""
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
        }

    @pytest.mark.asyncio()
    async def test_successful_transformation(
        self,
        use_case,
        mock_transformation_engine,
        sample_job,
        sample_source_data,
        sample_transformation_rules,
        sample_transformed_data,
    ):
        """Test successful data transformation."""
        # Setup
        mock_transformation_engine.transform.return_value = sample_transformed_data

        # Execute
        result = await use_case.execute(
            sample_job,
            sample_source_data,
            sample_transformation_rules,
        )

        # Verify
        assert result == sample_transformed_data
        assert sample_job.status == JobStatus.TRANSFORMING
        mock_transformation_engine.transform.assert_called_once_with(
            sample_source_data,
            sample_transformation_rules,
        )

    @pytest.mark.asyncio()
    async def test_transformation_failure_marks_job_as_failed(
        self,
        use_case,
        mock_transformation_engine,
        sample_job,
        sample_source_data,
        sample_transformation_rules,
    ):
        """Test transformation failure marks job as failed and re-raises exception."""
        # Setup
        error_message = "Invalid transformation rule"
        mock_transformation_engine.transform.side_effect = Exception(error_message)

        # Execute and verify exception is raised
        with pytest.raises(Exception, match=error_message):
            await use_case.execute(
                sample_job,
                sample_source_data,
                sample_transformation_rules,
            )

        # Verify job is marked as failed
        assert sample_job.status == JobStatus.FAILED
        assert sample_job.error_message == f"Failed to transform data: {error_message}"
        assert sample_job.completed_at is not None

    @pytest.mark.asyncio()
    async def test_job_status_transition(
        self,
        use_case,
        mock_transformation_engine,
        sample_source_data,
        sample_transformation_rules,
        sample_transformed_data,
    ):
        """Test that job status transitions correctly during transformation."""
        # Create job in FETCHING state
        job = TransformationJob()
        job.mark_as_fetching()
        assert job.status == JobStatus.FETCHING

        # Setup successful transformation
        mock_transformation_engine.transform.return_value = sample_transformed_data

        # Execute
        await use_case.execute(job, sample_source_data, sample_transformation_rules)

        # Verify status changed to TRANSFORMING
        assert job.status == JobStatus.TRANSFORMING

    @pytest.mark.asyncio()
    async def test_transformation_with_empty_rules(
        self,
        use_case,
        mock_transformation_engine,
        sample_job,
        sample_source_data,
    ):
        """Test transformation with empty rules list."""
        # Setup
        empty_rules = []
        expected_result = {"transformed": True}
        mock_transformation_engine.transform.return_value = expected_result

        # Execute
        result = await use_case.execute(sample_job, sample_source_data, empty_rules)

        # Verify
        assert result == expected_result
        mock_transformation_engine.transform.assert_called_once_with(
            sample_source_data,
            empty_rules,
        )

    @pytest.mark.asyncio()
    async def test_transformation_with_complex_data(
        self,
        use_case,
        mock_transformation_engine,
        sample_job,
    ):
        """Test transformation with complex nested data structures."""
        # Setup complex source data
        complex_source_data = {
            "orders": [
                {
                    "id": "order_1",
                    "customer": {
                        "name": "John Doe",
                        "address": {
                            "street": "123 Main St",
                            "city": "New York",
                            "country": "USA",
                        },
                    },
                    "items": [
                        {"product": "Laptop", "price": 999.99, "quantity": 1},
                        {"product": "Mouse", "price": 29.99, "quantity": 2},
                    ],
                },
            ],
        }

        complex_rules = [
            {
                "type": "extract_field",
                "source_field": "orders[].customer.name",
                "target_field": "customers[].name",
            },
            {
                "type": "format_address",
                "source_fields": [
                    "orders[].customer.address.street",
                    "orders[].customer.address.city",
                ],
                "target_field": "customers[].formatted_address",
            },
        ]

        expected_result = {
            "customers": [
                {"name": "John Doe", "formatted_address": "123 Main St, New York"},
            ],
        }

        mock_transformation_engine.transform.return_value = expected_result

        # Execute
        result = await use_case.execute(sample_job, complex_source_data, complex_rules)

        # Verify
        assert result == expected_result
        mock_transformation_engine.transform.assert_called_once_with(
            complex_source_data,
            complex_rules,
        )

    @pytest.mark.asyncio()
    async def test_multiple_transformations(
        self,
        mock_transformation_engine,
        sample_source_data,
        sample_transformation_rules,
        sample_transformed_data,
    ):
        """Test multiple transformation operations with different jobs."""
        use_case = TransformDataUseCase(
            transformation_engine=mock_transformation_engine,
        )
        mock_transformation_engine.transform.return_value = sample_transformed_data

        # Create multiple jobs
        job1 = TransformationJob(customer_id="customer1", config_name="config1")
        job1.mark_as_fetching()

        job2 = TransformationJob(customer_id="customer2", config_name="config2")
        job2.mark_as_fetching()

        # Execute multiple transformations
        result1 = await use_case.execute(
            job1,
            sample_source_data,
            sample_transformation_rules,
        )
        result2 = await use_case.execute(
            job2,
            sample_source_data,
            sample_transformation_rules,
        )

        # Verify
        assert result1 == sample_transformed_data
        assert result2 == sample_transformed_data
        assert job1.status == JobStatus.TRANSFORMING
        assert job2.status == JobStatus.TRANSFORMING
        assert mock_transformation_engine.transform.call_count == 2
