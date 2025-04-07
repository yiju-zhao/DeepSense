<<<<<<< HEAD:Backend/app/main.py
import sys
from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from database import SessionLocal, engine
import models.models as models
=======
import logging

from fastapi import FastAPI
>>>>>>> origin/main:Backend/main.py
from fastapi.middleware.cors import CORSMiddleware
from api import api_router
import logging

<<<<<<< HEAD:Backend/app/main.py
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
# Create logger for this module
logger = logging.getLogger(__name__)

# Initialize FastAPI app first
app = FastAPI()
models.Base.metadata.create_all(bind=engine)
=======
from app.api import api_router, add_error_handlers, add_logging_middleware
from app.core.config import settings
from app.core.logging import setup_logging
>>>>>>> origin/main:Backend/main.py

# Set up logging
setup_logging()
logger = logging.getLogger("deepsight")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

<<<<<<< HEAD:Backend/app/main.py
# Register API router
app.include_router(api_router, prefix="/api/v1")

# Then include the frontend adapter router
from api.routes.frontend_adapter import router as frontend_adapter_router
app.include_router(frontend_adapter_router, prefix="/api/v1")
=======
# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
>>>>>>> origin/main:Backend/main.py

# Add logging middleware
add_logging_middleware(app)

# Add error handlers
add_error_handlers(app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "status": "success",
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": "0.1.0",
        "docs": f"{settings.API_V1_STR}/docs",
    }

<<<<<<< HEAD:Backend/app/main.py
@app.post("/conferences", response_model=ConferenceModel)
async def create_conference(db: db_dependency, conference: ConferenceBase):
    db_conference = models.Conference(**conference.model_dump())
    db.add(db_conference)
    db.commit()
    db.refresh(db_conference)
    return db_conference
=======

@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {
        "status": "success",
        "message": "Healthy",
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.PROJECT_NAME} API")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
>>>>>>> origin/main:Backend/main.py
