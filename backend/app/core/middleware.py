"""
Application Middleware Components
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting a unique X-Request-ID into each request/response
    and logging execution timing.
    """
    async def dispatch(self, request: Request, call_next):
        # Retrieve or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response: Response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
            
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"-> status={response.status_code} ({process_time:.2f}ms)"
            )
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"FAILED with unhandled exception: {exc} ({process_time:.2f}ms)"
            )
            raise exc
