"""
JewelMind FastAPI Application Entrypoint
Phase 1 Architecture & Technical Foundation Service
"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger
from app.core.middleware import RequestContextMiddleware
from app.schemas.common import ErrorResponse, ErrorDetail

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Custom Middleware
app.add_middleware(RequestContextMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    request_id = getattr(request.state, "request_id", None)
    logger.warning(f"[{request_id}] Handled AppException: {exc.code} - {exc.message}")
    
    error_payload = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    logger.warning(f"[{request_id}] Validation error on {request.url.path}: {exc.errors()}")
    
    error_payload = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details=jsonable_encoder(exc.errors()),
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload.model_dump(mode="json"),
    )



@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.exception(f"[{request_id}] Unhandled Server Error on {request.url.path}: {exc}")
    
    # In production, never expose internal details
    message = "An internal server error occurred."
    details = str(exc) if settings.DEBUG else None
    
    error_payload = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message=message,
            details=details,
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(),
    )


# Mount Versioned API V1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# Legacy & Root Endpoints (Backward compatibility)
@app.get("/", tags=["General"])
async def root():
    """
    Root endpoint returning service identity.
    """
    return {
        "service": "JewelMind API",
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Base health check endpoint for backward compatibility.
    """
    return {
        "status": "ok",
        "service": "JewelMind API",
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
    }
