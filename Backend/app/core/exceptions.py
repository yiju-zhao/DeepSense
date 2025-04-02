from typing import Any, Dict, Optional

class DeepSightException(Exception):
    """Base exception for all custom exceptions in the DeepSight application."""
    
    def __init__(
        self, 
        message: str = "An error occurred", 
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class NotFoundException(DeepSightException):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self, 
        message: str = "Resource not found", 
        code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=404, details=details)

class ValidationError(DeepSightException):
    """Exception raised when validation fails."""
    
    def __init__(
        self, 
        message: str = "Validation error", 
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=422, details=details)

class AuthenticationError(DeepSightException):
    """Exception raised when authentication fails."""
    
    def __init__(
        self, 
        message: str = "Authentication failed", 
        code: str = "AUTHENTICATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=401, details=details)

class AuthorizationError(DeepSightException):
    """Exception raised when authorization fails."""
    
    def __init__(
        self, 
        message: str = "Not authorized", 
        code: str = "AUTHORIZATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=403, details=details)

class DatabaseError(DeepSightException):
    """Exception raised when a database operation fails."""
    
    def __init__(
        self, 
        message: str = "Database operation failed", 
        code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=500, details=details)

class DuplicateError(DeepSightException):
    """Exception raised when a duplicate resource is detected."""
    
    def __init__(
        self, 
        message: str = "Resource already exists", 
        code: str = "DUPLICATE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=409, details=details)

class ExternalServiceError(DeepSightException):
    """Exception raised when an external service call fails."""
    
    def __init__(
        self, 
        message: str = "External service error", 
        code: str = "EXTERNAL_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=502, details=details)