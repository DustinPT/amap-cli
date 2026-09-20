"""Custom error types used by the CLI."""

from __future__ import annotations

from typing import Any


class AmapCliError(Exception):
    """Base exception with a stable machine-readable payload."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "CLI_ERROR",
        details: Any | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details
        self.exit_code = exit_code

    def to_dict(self) -> dict[str, Any]:
        """Convert the error to the unified JSON output shape."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(AmapCliError):
    """Raised when command arguments fail validation."""

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(
            message,
            code="INVALID_ARGUMENT",
            details=details,
            exit_code=2,
        )


class ConfigError(AmapCliError):
    """Raised when configuration is missing or invalid."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "CONFIG_ERROR",
        details: Any | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details, exit_code=1)


class MissingConfigError(ConfigError):
    """Raised when a required config item has not been configured yet."""

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(message, code="MISSING_CONFIG", details=details)


class ApiRequestError(AmapCliError):
    """Raised when the HTTP request to Amap cannot be completed."""

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(
            message,
            code="API_REQUEST_ERROR",
            details=details,
            exit_code=1,
        )


class ApiResponseError(AmapCliError):
    """Raised when the Amap API returns a business-level failure."""

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(
            message,
            code="API_RESPONSE_ERROR",
            details=details,
            exit_code=1,
        )
