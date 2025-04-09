from database import engine, Base
import logging
import asyncio

# Import all models to ensure they're registered
import models.models

# Explicitly import Conference and ConferenceInstance to ensure they're registered
from models.models import Conference, ConferenceInstance
from models.tasks import (
    CrawlerTask,
    TaskExecution,
    ArxivPaper,
    Publication,
    PaperScores,
    SOTAContext,
)

logger = logging.getLogger(__name__)


async def init_db():
    """Initialize the database by creating all tables."""
    logger.info("Creating database tables...")

    # Create all tables using SQLAlchemy Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
