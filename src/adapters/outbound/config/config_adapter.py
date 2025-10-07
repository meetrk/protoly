# src/adapters/outbound/config/config_adapter.py
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import ValidationError, validate

from ....infrastructure.error_handling.exceptions import (
    ConfigNotFoundError,
    ConfigValidationError,
)


class FileConfigAdapter:
    """Adapter for loading configuration from YAML/JSON files."""

    def __init__(self, config_base_path: str, schema_path: str):
        """
        Initialize config adapter.

        Args:
            config_base_path: Base directory for customer configs
            schema_path: Path to JSON schema for validation
        """
        self.config_base_path = Path(config_base_path)
        self.schema_path = Path(schema_path)
        self._schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any]:
        """Load JSON schema for config validation."""
        with open(self.schema_path) as f:
            return json.load(f)

    def load_config(self, customer_id: str, config_name: str) -> dict[str, Any]:
        """
        Load customer configuration.

        Args:
            customer_id: Customer identifier
            config_name: Configuration file name

        Returns:
            Validated configuration dictionary

        Raises:
            ConfigNotFoundError: If config doesn't exist
            ConfigValidationError: If config is invalid
        """
        # Build config file path
        config_path = self.config_base_path / customer_id / f"{config_name}.yaml"

        if not config_path.exists():
            raise ConfigNotFoundError(f"Config not found: {config_path}")

        try:
            # Load YAML config
            with open(config_path) as f:
                config = yaml.safe_load(f)

            # Validate against schema
            validate(instance=config, schema=self._schema)

            return config

        except ValidationError as e:
            raise ConfigValidationError(
                f"Invalid config: {e.message}",
            ) from e
        except Exception as e:
            raise ConfigValidationError(
                f"Failed to load config: {str(e)}",
            ) from e
