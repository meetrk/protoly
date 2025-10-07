# src/infrastructure/error_handling/exceptions.py


class SourceFetchError(Exception):
    """Raised when fetching from source API fails."""

    pass


class TransformationError(Exception):
    """Raised when data transformation fails."""

    pass


class DeliveryError(Exception):
    """Raised when delivering to destination fails."""

    pass


class ConfigNotFoundError(Exception):
    """Raised when configuration file is not found."""

    pass


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass
