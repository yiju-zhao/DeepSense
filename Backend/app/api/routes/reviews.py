from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import SessionLocal
from models.tasks import ArxivPaper, PaperScores, StandardResponse
from core.review_arxiv_paper import ReviewArxivPaper

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/publications/{publication_id}", response_model=StandardResponse)
async def review_publication(db: db_dependency, publication_id: str):
    """
    Generate AI review for a specific publication
    """
    # Check if publication has already been reviewed
    scores = db.query(PaperScores).filter(PaperScores.paper_id == publication_id).first()

    if scores and scores.paper_id:
        logger.info(f"Publication {publication_id} already has review scores")
        return StandardResponse(
            success=True,
            message="Publication review already exists",
            data={"scores": scores},
        )
    
    # Generate review for unprocessed publication
    paper = db.query(ArxivPaper).filter(ArxivPaper.arxiv_id == publication_id).first()
    if not paper:
        logger.error(f"Publication {publication_id} not found")
        return StandardResponse(
            success=False, 
            message="Publication not found", 
            data={}
        )
    
    # Process the publication with AI review
    arxiv_review = ReviewArxivPaper()
    score = arxiv_review.process(paper)
    
    if not score:
        logger.error(f"Failed to generate review for publication {publication_id}")
        return StandardResponse(
            success=False, 
            message="Failed to generate review", 
            data={}
        )

    return StandardResponse(
        success=True,
        message="Publication review generated successfully",
        data={"scores": score},
    )


@router.post("/publications/batch", response_model=StandardResponse)
def review_publications_batch(db: db_dependency):
    """
    Generate AI reviews for all unprocessed publications in batch
    """
    # Find publications without reviews
    unprocessed_papers = (
        db.query(ArxivPaper)
        .outerjoin(PaperScores, ArxivPaper.arxiv_id == PaperScores.paper_id)
        .filter(PaperScores.paper_id.is_(None))
        .order_by(desc(ArxivPaper.published))
        .all()
    )
    
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
            message="Failed to process publications in batch",
            data={},
        )
    
    if len(scores) != len(unprocessed_papers):
        logger.warning(f"Processed {len(scores)} publications out of {len(unprocessed_papers)} requested")
        return StandardResponse(
            success=False,
            message=f"Processed {len(scores)} publications out of {len(unprocessed_papers)} requested",
            data={"scores": scores},
        )
    
    return StandardResponse(
        success=True,
        message=f"Successfully processed {len(scores)} publications",
        data={"scores": scores},
    ) 