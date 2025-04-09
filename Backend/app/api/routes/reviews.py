from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.tasks import ArxivPaper, PaperScores, StandardResponse
from core.review_arxiv_paper import ReviewArxivPaper

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])

# Use the async get_db dependency
db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.post("/publications/{publication_id}", response_model=StandardResponse)
async def review_publication(db: db_dependency, publication_id: str):
    """
    Generate AI review for a specific publication
    """
    # Check if publication has already been reviewed
    scores_query = select(PaperScores).filter(PaperScores.paper_id == publication_id)
    scores_result = await db.execute(scores_query)
    scores = scores_result.scalar_one_or_none()

    if scores and scores.paper_id:
        logger.info(f"Publication {publication_id} already has review scores")
        return StandardResponse(
            success=True,
            message="Publication review already exists",
            data={"scores": scores},
        )

    # Generate review for unprocessed publication
    paper_query = select(ArxivPaper).filter(ArxivPaper.arxiv_id == publication_id)
    paper_result = await db.execute(paper_query)
    paper = paper_result.scalar_one_or_none()

    if not paper:
        logger.error(f"Publication {publication_id} not found")
        return StandardResponse(success=False, message="Publication not found", data={})

    # Process the publication with AI review
    arxiv_review = ReviewArxivPaper()
    score = arxiv_review.process(paper)

    if not score:
        logger.error(f"Failed to generate review for publication {publication_id}")
        return StandardResponse(
            success=False, message="Failed to generate review", data={}
        )

    return StandardResponse(
        success=True,
        message="Publication review generated successfully",
        data={"scores": score},
    )


@router.post("/publications/batch", response_model=StandardResponse)
async def review_publications_batch(db: db_dependency):
    """
    Generate AI reviews for all unprocessed publications in batch
    """
    # Find publications without reviews
    unprocessed_query = (
        select(ArxivPaper)
        .outerjoin(PaperScores, ArxivPaper.arxiv_id == PaperScores.paper_id)
        .filter(PaperScores.paper_id.is_(None))
        .order_by(desc(ArxivPaper.published))
    )

    unprocessed_result = await db.execute(unprocessed_query)
    unprocessed_papers = unprocessed_result.scalars().all()

    if not unprocessed_papers:
        logger.info("No unprocessed publications found")
        return StandardResponse(
            success=True,
            message="No unprocessed publications found",
            data={},
        )

    logger.info(f"Found {len(unprocessed_papers)} unprocessed publications")

    # Process publications in batch
    arxiv_review = ReviewArxivPaper()
    scores = arxiv_review.process_batch(unprocessed_papers)

    if not scores or len(scores) == 0:
        logger.error("Batch processing failed")
        return StandardResponse(
            success=False,
            message="Batch processing failed",
            data={},
        )

    logger.info(f"Successfully processed {len(scores)} publications")
    return StandardResponse(
        success=True,
        message=f"Successfully processed {len(scores)} publications",
        data={"scores": scores},
    )
