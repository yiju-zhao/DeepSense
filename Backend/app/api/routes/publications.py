from datetime import date, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Query

from database import SessionLocal
from models.tasks import ArxivPaper, PaperScores, Publication, StandardResponse

router = APIRouter(prefix="/publications", tags=["publications"])

import logging
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/{publication_id}", response_model=StandardResponse)
async def get_publication(db: db_dependency, publication_id: str):
    """
    Retrieve a specific publication by ID with its evaluation scores
    """
    publication = (
        db.query(Publication)
        .outerjoin(PaperScores, Publication.paper_id == PaperScores.paper_id)
        .filter(Publication.paper_id == publication_id)
        .first()
    )
    # NOTE: ArxivPaper contains metadata like authors and affiliations not yet in Publication
    arxiv_paper = db.query(ArxivPaper).filter(ArxivPaper.arxiv_id == publication_id).first()

    if publication and arxiv_paper:
        # Avoid returning large raw text fields
        publication.content_raw_text = ""
        publication.reference_raw_text = ""
        return_data = {
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

        return StandardResponse(
            success=True,
            message="Publication retrieved successfully",
            data=return_data,
        )
    else:
        return StandardResponse(
            success=False, message="Publication not found", data={}
        )


@router.get("", response_model=StandardResponse)
async def get_publications(
    db: db_dependency,
    start_date: Optional[date] = Query(
        None, description="Start date to filter by (yyyy-mm-dd)"
    ),
    end_date: Optional[date] = Query(
        None, description="End date to filter by (yyyy-mm-dd)"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    sort_by: Optional[str] = Query(
        "publish_date",
        description="Field to sort by: 'publish_date' or 'weighted_score'",
    ),
    order: Optional[str] = Query("desc", description="Sort order: 'asc' or 'desc'"),
):
    """
    Retrieve publications from the database with pagination and filtering options
    """
    if not start_date:
        start_date = datetime(1970, 1, 1).date()

    if not end_date:
        end_date = datetime.now().date()

    publication_list = (
        db.query(Publication)
        .filter(
            Publication.paper_id != None,
            Publication.publish_date >= start_date,
            Publication.publish_date <= end_date,
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not publication_list:
        return StandardResponse(success=False, message="No publications found", data={})
    
    logger.info(f"Found {len(publication_list)} publications matching criteria")
    return_data = []
    
    for publication in publication_list:
        arxiv_paper = (
            db.query(ArxivPaper)
            .filter(ArxivPaper.arxiv_id == publication.paper_id)
            .first()
        )
        
        if not arxiv_paper:
            continue
            
        item_data = {
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
        return_data.append(item_data)

    # Sort publications by weighted score (highest first) then by date
    sorted_data = sorted(
        return_data,
        key=lambda x: (x["weighted_score"], x["publish_date"]),
        reverse=True if order.lower() == "desc" else False,
    )

    total_count = len(sorted_data)
    return StandardResponse(
        success=True,
        message=f"Retrieved {total_count} publications",
        data={"publications": sorted_data, "count": total_count},
    ) 