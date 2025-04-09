import sys
from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict
from database import SessionLocal, engine, Base, get_db
import models.models as models
from fastapi.middleware.cors import CORSMiddleware
from api import api_router
import logging
import asyncio
from db_init import init_db

# Import all SQLAlchemy models to ensure they're registered with metadata
from models.models import Conference, ConferenceInstance
from models.tasks import (
    CrawlerTask,
    TaskExecution,
    ArxivPaper,
    Publication,
    PaperScores,
    SOTAContext,
    TaskStatus,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
)
# Create logger for this module
logger = logging.getLogger(__name__)

app = FastAPI()


# Initialize database
@app.on_event("startup")
async def startup_event():
    await init_db()


origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API router
app.include_router(api_router, prefix="/api/v1")


class ConferenceBase(BaseModel):
    name: str
    type: str
    description: str


class ConferenceModel(ConferenceBase):
    conference_id: int

    model_config = ConfigDict(from_attributes=True)


# Use the async get_db dependency
db_dependency = Annotated[AsyncSession, Depends(get_db)]


@app.post("/conferences", response_model=ConferenceModel)
async def create_conference(db: db_dependency, conference: ConferenceBase):
    db_conference = models.Conference(**conference.model_dump())
    db.add(db_conference)
    await db.commit()
    await db.refresh(db_conference)
    return db_conference


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
