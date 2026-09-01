"""
Common API Schemas & Response Wrappers
"""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable application error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(None, description="Detailed validation or context metadata")


class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: Optional[str] = Field(None, description="Correlation identifier for request tracing")


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT
    message: Optional[str] = None
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "JewelMind API"
    version: str
    environment: str
    database_configured: bool = False
