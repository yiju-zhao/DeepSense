import time
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response from the next middleware or endpoint handler
        """
        # Generate a unique request ID
        request_id = str(uuid4())
        
        # Add request ID to the request state
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Log request details
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log response details
            logger.info(
                f"Request completed: {request.method} {request.url.path} {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error details
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": process_time
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise


class SlowRequestMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging slow requests.
    """
    
    def __init__(self, app: FastAPI, threshold: float = 1.0):
        """
        Initialize the middleware.
        
        Args:
            app: FastAPI application
            threshold: Threshold in seconds for slow requests
        """
        super().__init__(app)
        self.threshold = threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log if it's slow.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response from the next middleware or endpoint handler
        """
        # Start timer
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log if the request is slow
        if process_time > self.threshold:
            request_id = getattr(request.state, "request_id", None)
            
            logger.warning(
                f"Slow request: {request.method} {request.url.path} ({process_time:.2f}s)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "threshold": self.threshold
                }
            )
        
        return response


def add_logging_middleware(app: FastAPI) -> None:
    """
    Add logging middleware to the FastAPI application.
    
    Args:
        app: FastAPI application
    """
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SlowRequestMiddleware, threshold=1.0)