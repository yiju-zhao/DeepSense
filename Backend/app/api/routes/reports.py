from datetime import date, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from models.tasks import ArxivPaper, PaperScores, Publication, StandardResponse
from core.review_arxiv_paper import ReviewArxivPaper

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/daily", response_model=StandardResponse)
async def get_daily_report(
    db: db_dependency,
    date: Optional[date] = Query(
        None, description="Report date (yyyy-mm-dd). Defaults to today if not specified"
    ),
):
    """
    Get daily report of top publications for a specific date
    """
    if not date:
        date = datetime.now().date()
    
    logger.info(f"Generating daily report for date: {date}")
    
    # Get publications for the specified date
    publication_list = (
        db.query(Publication)
        .filter(
            Publication.paper_id != None,
            Publication.publish_date >= date,
            Publication.publish_date <= date,
        )
        .limit(10)  # Top 10 publications for the day
        .all()
    )
    
    if not publication_list:
        return StandardResponse(
            success=False, 
            message=f"No publications found for {date}", 
            data={}
        )
    
    logger.info(f"Found {len(publication_list)} publications for daily report")
    
    # Get enhanced publication data with scores
    publication_data = []
    for publication in publication_list:
        arxiv_paper = (
            db.query(ArxivPaper)
            .filter(ArxivPaper.arxiv_id == publication.paper_id)
            .first()
        )
        
        if not arxiv_paper:
            continue
            
        publication_info = {
            "publication_id": publication.paper_id,
            "publish_date": publication.publish_date,
            "title": publication.title,
            "pdf_url": publication.pdf_url,
            "abstract": publication.abstract,
            "author": arxiv_paper.authors,
            "conclusion": publication.conclusion,
            "traige_qa": publication.triage_qa,
            "scores": (
                publication.scores
                if publication.scores
                else "{'review_status':'pending','error_message':'not processed yet'}"
            ),
            "weighted_score": (
                publication.scores.weighted_score if publication.scores else 0
            ),
        }
        publication_data.append(publication_info)

    # Sort publications by score (highest first)
    sorted_publications = sorted(
        publication_data,
        key=lambda x: (x["weighted_score"], x["publish_date"]),
        reverse=True,
    )

    top_publications = sorted_publications[:10]
    total_count = len(top_publications)
    
    # Generate AI report summarizing the top publications
    logger.info(f"Generating AI report for {total_count} publications")
    arxiv_review = ReviewArxivPaper()
    report = arxiv_review.get_ai_daily_report(
        report_day=date, 
        top_k=total_count, 
        context=str(top_publications)
    )
    
    return StandardResponse(
        success=True,
        message=f"Daily report generated for {date}",
        data=report,
    ) 