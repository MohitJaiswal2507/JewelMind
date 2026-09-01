"""
Centralized Application Exception Definitions
"""

from typing import Any, Optional, Dict


class AppException(Exception):
    """
    Base application exception with error code and structured metadata.
    """
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ResourceNotFoundException(AppException):
    """
    Raised when a requested resource is not found.
    """
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)},
        )


class ValidationException(AppException):
    """
    Raised when business validation rules fail.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class ServiceUnavailableException(AppException):
    """
    Raised when an external or worker service is unreachable.
    """
    def __init__(self, service_name: str, reason: Optional[str] = None):
        super().__init__(
            message=f"Service '{service_name}' is currently unavailable. {reason or ''}".strip(),
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service_name},
        )
