from typing import Any, Dict, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.api.errors.http_error import DeepSightHTTPException
from app.core.exceptions import DeepSightException
from app.core.logging import logger


def add_error_handlers(app: FastAPI) -> None:
    """
    Add error handlers to the FastAPI application.
    
    Args:
        app: FastAPI application
    """
    
    @app.exception_handler(DeepSightHTTPException)
    async def deepsight_http_exception_handler(
        request: Request, exc: DeepSightHTTPException
    ) -> JSONResponse:
        """
        Handle DeepSightHTTPException.
        
        Args:
            request: FastAPI request
            exc: DeepSightHTTPException
            
        Returns:
            JSONResponse with error details
        """
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(exc.code, exc.detail)
        )
    
    @app.exception_handler(DeepSightException)
    async def deepsight_exception_handler(
        request: Request, exc: DeepSightException
    ) -> JSONResponse:
        """
        Handle DeepSightException.
        
        Args:
            request: FastAPI request
            exc: DeepSightException
            
        Returns:
            JSONResponse with error details
        """
        logger.error(
            f"DeepSightException: {exc.message}",
            extra={"details": exc.details},
            exc_info=True
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(exc.code, exc.message, exc.details)
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle RequestValidationError.
        
        Args:
            request: FastAPI request
            exc: RequestValidationError
            
        Returns:
            JSONResponse with error details
        """
        errors = exc.errors()
        logger.warning(
            "Validation error",
            extra={"errors": errors},
            exc_info=False
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=format_error_response(
                "VALIDATION_ERROR",
                "Validation error",
                {"errors": errors}
            )
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic ValidationError.
        
        Args:
            request: FastAPI request
            exc: ValidationError
            
        Returns:
            JSONResponse with error details
        """
        errors = exc.errors()
        logger.warning(
            "Pydantic validation error",
            extra={"errors": errors},
            exc_info=False
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=format_error_response(
                "VALIDATION_ERROR",
                "Validation error",
                {"errors": errors}
            )
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """
        Handle SQLAlchemyError.
        
        Args:
            request: FastAPI request
            exc: SQLAlchemyError
            
        Returns:
            JSONResponse with error details
        """
        logger.error(
            f"Database error: {str(exc)}",
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=format_error_response(
                "DATABASE_ERROR",
                "Database error",
                {"message": str(exc)}
            )
        )
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle unhandled exceptions.
        
        Args:
            request: FastAPI request
            exc: Exception
            
        Returns:
            JSONResponse with error details
        """
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=format_error_response(
                "INTERNAL_SERVER_ERROR",
                "Internal server error"
            )
        )


def format_error_response(
    code: str,
    message: str,
    details: Dict[str, Any] = None
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Format error response.
    
    Args:
        code: Error code
        message: Error message
        details: Error details
        
    Returns:
        Formatted error response
    """
    response = {
        "status": "error",
        "error": {
            "code": code,
            "message": message
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return response