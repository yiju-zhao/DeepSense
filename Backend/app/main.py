import sys
from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from database import SessionLocal, engine
import models.models as models
from fastapi.middleware.cors import CORSMiddleware
from api import api_router
import logging

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

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:3000",
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/conferences", response_model=ConferenceModel)
async def create_conference(db: db_dependency, conference: ConferenceBase):
    db_conference = models.Conference(**conference.model_dump())
    db.add(db_conference)
    db.commit()
    db.refresh(db_conference)
    return db_conference
