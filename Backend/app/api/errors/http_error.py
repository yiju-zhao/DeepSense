from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class DeepSightHTTPException(HTTPException):
    """
    Custom HTTP exception for DeepSight API.
    """
    
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
        code: str = "ERROR"
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            status_code: HTTP status code
            detail: Error detail
            headers: HTTP headers
            code: Error code
        """
        self.code = code
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class BadRequestException(DeepSightHTTPException):
    """
    Exception for 400 Bad Request errors.
    """
    
    def __init__(
        self,
        detail: Any = "Bad request",
        headers: Optional[Dict[str, Any]] = None,
        code: str = "BAD_REQUEST"
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            detail: Error detail
            headers: HTTP headers
            code: Error code
        """
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
            code=code
        )


class UnauthorizedException(DeepSightHTTPException):
    """
    Exception for 401 Unauthorized errors.
    """
    
    def __init__(
        self,
        detail: Any = "Not authenticated",
        headers: Optional[Dict[str, Any]] = None,
        code: str = "UNAUTHORIZED"
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            detail: Error detail
            headers: HTTP headers
            code: Error code
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"},
            code=code
        )


class ForbiddenException(DeepSightHTTPException):
    """
    Exception for 403 Forbidden errors.
    """
    
    def __init__(
        self,
        detail: Any = "Not enough permissions",
        headers: Optional[Dict[str, Any]] = None,
        code: str = "FORBIDDEN"
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            detail: Error detail
            headers: HTTP headers
            code: Error code
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
            code=code
        )


class NotFoundException(DeepSightHTTPException):
    """
    Exception for 404 Not Found errors.
    """
    
    def __init__(
        self,
        detail: Any = "Resource not found",
        headers: Optional[Dict[str, Any]] = None,
        code: str = "NOT_FOUND"
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            detail: Error detail
            headers: HTTP headers
            code: Error code
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
            code=code
        )


class ConflictException(DeepSightHTTPException):
    """
    Exception for 409 Conflict errors.
    """
    
    def __init__(
        self,
        detail: Any = "Resource already exists",
        headers: Optional[Dict[str, Any]] = None,
        code: str = "CONFLICT"
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            detail: Error detail
            headers: HTTP headers
            code: Error code
        """
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers,
            code=code
        )


class UnprocessableEntityException(DeepSightHTTPException):
    """
    Exception for 422 Unprocessable Entity errors.
    """
    
    def __init__(
        self,
        detail: Any = "Validation error",
        headers: Optional[Dict[str, Any]] = None,
        code: str = "UNPROCESSABLE_ENTITY"
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            detail: Error detail
            headers: HTTP headers
            code: Error code
        """
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers,
            code=code
        )


class InternalServerErrorException(DeepSightHTTPException):
    """
    Exception for 500 Internal Server Error errors.
    """
    
    def __init__(
        self,
        detail: Any = "Internal server error",
        headers: Optional[Dict[str, Any]] = None,
        code: str = "INTERNAL_SERVER_ERROR"
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            detail: Error detail
            headers: HTTP headers
            code: Error code
        """
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers,
            code=code
        )