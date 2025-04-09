# DeepSight Backend

## Table of Contents
- [Quick Start Guide](#quick-start-guide)
- [Architecture Overview](#architecture-overview)
- [Directory Structure](#directory-structure)
- [Data Models](#data-models)

## Quick Start Guide

### Prerequisites
- Python 3.9 or higher
- PostgreSQL 14 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yiju-zhao/DeepSense.git
cd DeepSense/Backend
```

2. Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows, use: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the `app` directory with the following content:
```env
DATABASE_URL=your-database-url-here
OPENAI_API_KEY=your-openai-api-key-here
```

<!-- 5. Initialize the database:
```bash
# Create database migrations
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
``` -->

### Starting the Backend Server

1. Start the FastAPI server:
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### API Documentation

The API documentation is available in two formats:

1. **Swagger UI (Interactive)**
   - URL: `http://localhost:8000/docs`
   - Interactive API documentation where you can try out the endpoints
   - Features:
     - Try out API endpoints directly in the browser
     - View request/response schemas
     - See authentication requirements
     - Test different parameters

2. **ReDoc (Read-only)**
   - URL: `http://localhost:8000/redoc`
   - Clean, organized documentation
   - Features:
     - Better readability
     - Organized by tags
     - Detailed schema information
     - Search functionality

### Testing the API

1. **Using Swagger UI**
   - Open `http://localhost:8000/docs` in your browser
   - Click on any endpoint to expand it
   - Click "Try it out"
   - Fill in the required parameters
   - Click "Execute" to test the endpoint

2. **Using ReDoc**
   - Open `http://localhost:8000/redoc` in your browser
   - Browse through the available endpoints
   - Use the search functionality to find specific endpoints
   - View detailed request/response schemas

3. **Using curl**
Example for authentication:
```bash
# Register a new user
curl -X 'POST' \
  'http://localhost:8000/api/v1/auth/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "testuser",
  "email": "test@example.com",
  "password": "testpassword123",
  "full_name": "Test User"
}'

# Login
curl -X 'POST' \
  'http://localhost:8000/api/v1/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "testuser",
  "password": "testpassword123"
}'
```

### Common Issues and Solutions

1. **Database Connection Issues**
   - Ensure PostgreSQL is running
   - Verify database configuration in `config.py` file
   - Check if the database exists

2. **Port Already in Use**
   - Change the port in the uvicorn command:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

3. **Module Not Found Errors**
   - Ensure you're in the correct directory
   - Verify all dependencies are installed
   - Check if virtual environment is activated

## Architecture Overview

The architecture will follow a layered approach:

1. **API Layer** - FastAPI endpoints with request/response models
2. **Authentication Layer** - JWT-based authentication and role-based authorization
3. **Service Layer** - Business logic implementation
4. **Repository Layer** - Data access abstraction
5. **Database Layer** - PostgreSQL with SQLAlchemy ORM

## Directory Structure

The project follows a clean, modular structure with clear separation of concerns:

```
DeepSight/Backend/
├── alembic/                  # Database migrations
│   ├── versions/             # Migration versions
│   ├── env.py                # Alembic environment
│   ├── script.py.mako        # Migration template
│   └── README                # Alembic usage instructions
├── app/
│   ├── api/                  # API endpoints
│   │   ├── dependencies/     # API dependencies (auth, pagination, etc.)
│   │   │   ├── auth.py       # Authentication dependencies
│   │   │   └── pagination.py # Pagination utilities
│   │   ├── errors/           # Error handling
│   │   │   ├── handlers.py   # Global exception handlers
│   │   │   └── http_error.py # HTTP exception classes
│   │   ├── middleware/       # Custom middleware
│   │   │   └── logging.py    # Request logging middleware
│   │   └── routes/           # API route definitions
│   │       ├── auth.py       # Authentication routes
│   │       └── ...           # Other route modules
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
│   │   ├── user.py           # User model
│   │   ├── conference.py     # Conference models
│   │   ├── paper.py          # Paper and related models
│   │   ├── session.py        # Session model
│   │   └── report.py         # Report and notebook models
│   ├── repositories/         # Repository pattern implementations
│   │   ├── base.py           # Base repository
│   │   ├── user.py           # User repository
│   │   ├── conference.py     # Conference repositories
│   │   ├── paper.py          # Paper repositories
│   │   ├── person.py         # Person repositories
│   │   ├── session.py        # Session repository
│   │   ├── report.py         # Report repositories
│   │   └── notebook.py       # Notebook repositories
│   ├── schemas/              # Pydantic schemas for request/response
│   │   ├── user.py           # User schemas
│   │   ├── conference.py     # Conference schemas
│   │   └── ...               # Other schema modules
│   ├── services/             # Business logic services
│   │   ├── base.py           # Base service
│   │   ├── user.py           # User service
│   │   └── ...               # Other service modules
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── alembic.ini               # Alembic configuration
├── main.py                   # Application entry point
├── .gitignore                # Git ignore file
└── requirements.txt          # Project dependencies
```

## Data Models

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



