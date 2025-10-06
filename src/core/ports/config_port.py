# src/core/ports/config_port.py
from typing import Any, Protocol


class ConfigPort(Protocol):
    """Port for loading and validating configuration."""

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
        ...
