# DeepSight Backend Design Plan

## Table of Contents
- [1. Architecture Overview](#1-architecture-overview)
- [2. Directory Structure](#2-directory-structure)
- [3. Data Models](#3-data-models)
- [4. Authentication & Authorization](#4-authentication--authorization)
- [5. API Design](#5-api-design)
- [6. Endpoints](#6-endpoints)
- [7. Async Database Operations](#7-async-database-operations)
- [8. Repository Pattern Implementation](#8-repository-pattern-implementation)
- [9. Service Layer Implementation](#9-service-layer-implementation)
- [10. Error Handling and Logging](#10-error-handling-and-logging)
- [11. Implementation Strategy](#11-implementation-strategy)
- [12. Technologies and Libraries](#12-technologies-and-libraries)
- [13. Security Considerations](#13-security-considerations)

## 1. Architecture Overview

The architecture will follow a layered approach:

1. **API Layer** - FastAPI endpoints with request/response models
2. **Authentication Layer** - JWT-based authentication and role-based authorization
3. **Service Layer** - Business logic implementation
4. **Repository Layer** - Data access abstraction
5. **Database Layer** - PostgreSQL with SQLAlchemy ORM

## 2. Directory Structure

```
DeepSight/Backend/
├── alembic/                  # Database migrations
├── app/
│   ├── api/                  # API endpoints
│   │   ├── dependencies/     # API dependencies (auth, pagination, etc.)
│   │   ├── errors/           # Error handling
│   │   ├── middleware/       # Custom middleware
│   │   └── routes/           # API route definitions
│   ├── core/                 # Core application components
│   │   ├── config.py         # Application configuration
│   │   ├── security.py       # Security utilities
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── logging.py        # Logging configuration
│   ├── db/                   # Database components
│   │   ├── base.py           # Base database setup
│   │   ├── session.py        # Database session management
│   │   └── transactions.py   # Transaction management
│   ├── models/               # SQLAlchemy models
│   ├── repositories/         # Repository pattern implementations
│   ├── schemas/              # Pydantic schemas for request/response
│   │   └── validators.py     # Custom validators
│   ├── services/             # Business logic services
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── alembic.ini               # Alembic configuration
├── main.py                   # Application entry point
└── requirements.txt          # Project dependencies
```

## 3. Data Models

We'll implement all the models from the reference implementation with some enhancements:

- User
- Conference
- ConferenceInstance
- Paper
- Author
- Affiliation
- Keyword
- Reference
- Session
- Speaker

Key relationships:
- Conference has many ConferenceInstances
- ConferenceInstance has many Papers and Sessions
- Paper has many Authors, Keywords, and References
- Author has many Affiliations
- Session has many Speakers

## 4. Authentication & Authorization

### 4.1 User Model

```python
# app/models/user.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Define roles as a relationship or as a column depending on your needs
    # For simplicity, we'll use a string column that stores comma-separated roles
    roles = Column(String, default="user")  # e.g., "user,editor,admin"
```

### 4.2 JWT-based Authentication

We'll implement JWT-based authentication with the following features:

1. User registration and login
2. Role-based access control (Admin, Editor, Viewer)
3. Token refresh mechanism
4. Password hashing with bcrypt
5. Endpoint protection with dependencies

### 4.3 Authentication Endpoints

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (invalidate token)

## 5. API Design

The API will follow RESTful principles with the following improvements:

### 5.1 Consistent Response Format

```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation successful"
}
```

### 5.2 Error Handling

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": { ... }
  }
}
```

### 5.3 Pagination

- Offset-based pagination for all list endpoints
- Customizable page size
- Metadata including total count, page count, etc.

### 5.4 Filtering and Sorting

- Query parameter-based filtering
- Multiple field sorting
- Search functionality

### 5.5 API Versioning

- URL-based versioning (e.g., `/api/v1/conferences`)

## 6. Endpoints

We'll implement the following API endpoints:

### 6.1 Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (invalidate token)

### 6.2 Conferences

- `GET /api/v1/conferences` - List all conferences
- `POST /api/v1/conferences` - Create a new conference
- `GET /api/v1/conferences/{id}` - Get conference details
- `PUT /api/v1/conferences/{id}` - Update conference
- `DELETE /api/v1/conferences/{id}` - Delete conference

### 6.3 Conference Instances

- `GET /api/v1/conferences/{id}/instances` - List instances for a conference
- `POST /api/v1/conferences/{id}/instances` - Create a new instance
- `GET /api/v1/instances/{id}` - Get instance details
- `PUT /api/v1/instances/{id}` - Update instance
- `DELETE /api/v1/instances/{id}` - Delete instance

### 6.4 Papers

- `GET /api/v1/instances/{id}/papers` - List papers for an instance
- `POST /api/v1/papers` - Create a new paper
- `GET /api/v1/papers/{id}` - Get paper details
- `PUT /api/v1/papers/{id}` - Update paper
- `DELETE /api/v1/papers/{id}` - Delete paper

### 6.5 Authors

- `GET /api/v1/authors` - List all authors
- `POST /api/v1/authors` - Create a new author
- `GET /api/v1/authors/{id}` - Get author details
- `PUT /api/v1/authors/{id}` - Update author
- `DELETE /api/v1/authors/{id}` - Delete author

### 6.6 Report & Notebook Management

- **Report Generation**
  - `POST /api/v1/reports` - Generate new report (AI agent)
  - `GET /api/v1/reports` - List all reports
  - `GET /api/v1/reports/{id}` - Get report details
  - `PUT /api/v1/reports/{id}` - Update report content
  - `DELETE /api/v1/reports/{id}` - Delete report
  - `POST /api/v1/reports/{id}/share` - Share report
  - `POST /api/v1/reports/{id}/versions` - Save report version

- **Notebook Operations**
  - `POST /api/v1/notebooks` - Create new notebook
  - `GET /api/v1/notebooks` - List all notebooks
  - `GET /api/v1/notebooks/{id}` - Get notebook details
  - `PUT /api/v1/notebooks/{id}` - Update notebook
  - `DELETE /api/v1/notebooks/{id}` - Delete notebook
  - `POST /api/v1/notebooks/{id}/share` - Share notebook
  - `POST /api/v1/notebooks/{id}/snapshots` - Save notebook state

### 6.7 Similar endpoints for Affiliations, Keywords, References, Sessions, and Speakers

## 7. Async Database Operations

We'll implement async database operations using SQLAlchemy 2.0's async features:

### 7.1 Async Database Session

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.get_database_url,
    echo=settings.DB_ECHO,
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_session() -> AsyncSession:
    """Get an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 7.2 Transaction Management

```python
# app/db/transactions.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from app.core.exceptions import DatabaseError
from app.core.logging import logger

@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Context manager for transaction management."""
    # Start a nested transaction (savepoint)
    async with session.begin():
        try:
            # Yield the session to the context block
            yield session
            # The transaction will be committed when the context block exits normally
        except Exception as e:
            # Log the error
            logger.error(
                f"Transaction error: {str(e)}",
                extra={"error": str(e)},
                exc_info=True
            )
            
            # The transaction will be rolled back automatically when an exception occurs
            # Re-raise as a DatabaseError
            if not isinstance(e, DatabaseError):
                raise DatabaseError(message=f"Database operation failed: {str(e)}", details={"original_error": str(e)})
            raise
```

## 8. Repository Pattern Implementation

### 8.1 Base Repository

The repository pattern provides an abstraction layer between the data access logic and the business logic of the application. The base repository will provide common CRUD operations:

- get(id) - Get a single record by ID
- get_multi(skip, limit, filters) - Get multiple records with pagination and filtering
- create(obj_in) - Create a new record
- update(db_obj, obj_in) - Update a record
- delete(id) - Delete a record by ID
- count(filters) - Count records with optional filtering

### 8.2 Specific Repository Implementations

Each entity will have its own repository that extends the base repository and adds specific methods:

- ConferenceRepository
- ConferenceInstanceRepository
- PaperRepository
- AuthorRepository
- AffiliationRepository
- KeywordRepository
- ReferenceRepository
- SessionRepository
- SpeakerRepository

### 8.3 Repository Factory

To manage repository creation and ensure proper session handling, we'll implement a repository factory that provides access to all repositories with a shared database session.

## 9. Service Layer Implementation

### 9.1 Base Service

The service layer contains the business logic of the application and uses repositories to access data. The base service will provide common functionality:

- get(id) - Get a single record by ID
- get_multi(skip, limit, filters) - Get multiple records with pagination and filtering
- create(obj_in) - Create a new record
- update(id, obj_in) - Update a record
- delete(id) - Delete a record
- count(filters) - Count records with optional filtering

### 9.2 Specific Service Implementations

Each entity will have its own service that extends the base service and adds specific business logic:

- ConferenceService
- ConferenceInstanceService
- PaperService
- AuthorService
- AffiliationService
- KeywordService
- ReferenceService
- SessionService
- SpeakerService

### 9.3 Service Dependencies

Services will be provided as dependencies in the FastAPI application using dependency injection.

## 10. Error Handling and Logging

### 10.1 Custom Exception Classes

We'll implement a hierarchy of custom exceptions to handle different types of errors:

- DeepSightException - Base exception for all custom exceptions
- NotFoundException - Exception raised when a resource is not found
- ValidationError - Exception raised when validation fails
- AuthenticationError - Exception raised when authentication fails
- AuthorizationError - Exception raised when authorization fails
- DatabaseError - Exception raised when a database operation fails
- DuplicateError - Exception raised when a duplicate resource is detected
- ExternalServiceError - Exception raised when an external service call fails

### 10.2 Global Exception Handler

We'll implement a global exception handler to catch all exceptions and return a consistent error response.

### 10.3 Structured Logging

We'll implement a structured logging system using Python's built-in logging module with JSON formatting.

### 10.4 Request Logging Middleware

We'll implement a middleware to log all incoming requests and their responses.

### 10.5 Performance Monitoring

We'll implement a middleware to track API performance and log slow requests.

## 11. Implementation Strategy

The implementation will be done in phases:

### Phase 1: Core Infrastructure
1. Set up project structure
2. Configure FastAPI application
3. Set up database connection and models
4. Implement authentication system
5. Create base repository and service classes

### Phase 2: Basic API Endpoints
1. Implement conference-related endpoints
2. Implement paper-related endpoints
3. Implement author-related endpoints
4. Add pagination and filtering

### Phase 3: Advanced Features
1. Implement remaining entity endpoints
2. Add advanced search capabilities
3. Implement data validation and error handling
4. Add database migrations with Alembic

### Phase 4: Testing and Documentation
1. Write unit and integration tests
2. Create API documentation with Swagger/OpenAPI
3. Add performance optimizations
4. Implement logging and monitoring

## 12. Technologies and Libraries

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **Alembic**: Database migrations
- **Passlib/bcrypt**: Password hashing
- **PyJWT**: JWT token handling
- **Pytest**: Testing framework
- **Uvicorn**: ASGI server
- **Python-dotenv**: Environment variable management

## 13. Security Considerations

1. **Input Validation**: Strict validation of all input data
2. **SQL Injection Protection**: Using ORM and parameterized queries
3. **Authentication**: Secure token-based authentication
4. **Authorization**: Role-based access control
5. **Password Security**: Bcrypt hashing with salt
6. **CORS**: Proper CORS configuration
7. **Rate Limiting**: Prevent abuse with rate limiting
8. **Secure Headers**: Implementation of security headers
