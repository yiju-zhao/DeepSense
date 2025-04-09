from datetime import date, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Query
from sqlalchemy import select, desc, asc

from database import get_db
from models.tasks import ArxivPaper, PaperScores, Publication, StandardResponse

router = APIRouter(prefix="/publications", tags=["publications"])

import logging

logger = logging.getLogger(__name__)

# Use the async get_db dependency
db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.get("/{publication_id}", response_model=StandardResponse)
async def get_publication(db: db_dependency, publication_id: str):
    """
    Retrieve a specific publication by ID with its evaluation scores
    """
    # Use select statements for async queries
    publication_query = (
        select(Publication)
        .outerjoin(PaperScores, Publication.paper_id == PaperScores.paper_id)
        .filter(Publication.paper_id == publication_id)
    )

    publication_result = await db.execute(publication_query)
    publication = publication_result.scalar_one_or_none()

    # Query for ArxivPaper
    arxiv_query = select(ArxivPaper).filter(ArxivPaper.arxiv_id == publication_id)
    arxiv_result = await db.execute(arxiv_query)
    arxiv_paper = arxiv_result.scalar_one_or_none()

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
        return StandardResponse(success=False, message="Publication not found", data={})


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

    # Build the query
    query = (
        select(Publication)
        .outerjoin(PaperScores, Publication.paper_id == PaperScores.paper_id)
        .filter(
            Publication.publish_date >= start_date, Publication.publish_date <= end_date
        )
    )

    # Apply sorting
    if sort_by == "weighted_score":
        if order == "desc":
            query = query.order_by(desc(PaperScores.weighted_score))
        else:
            query = query.order_by(asc(PaperScores.weighted_score))
    else:  # Default to publish_date
        if order == "desc":
            query = query.order_by(desc(Publication.publish_date))
        else:
            query = query.order_by(asc(Publication.publish_date))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute the query
    result = await db.execute(query)
    publications = result.scalars().all()

    # Format the response
    publications_data = []
    for pub in publications:
        # Avoid returning large raw text fields
        pub.content_raw_text = ""
        pub.reference_raw_text = ""

        pub_data = {
            "publication_id": pub.paper_id,
            "publish_date": pub.publish_date,
            "title": pub.title,
            "pdf_url": pub.pdf_url,
            "abstract": pub.abstract,
            "conclusion": pub.conclusion,
            "traige_qa": pub.triage_qa,
            "scores": (
                pub.scores
                if pub.scores
                else "{'review_status':'pending','error_message':'not processed yet'}"
            ),
            "weighted_score": (pub.scores.weighted_score if pub.scores else 0),
        }
        publications_data.append(pub_data)

    return StandardResponse(
        success=True,
        message=f"Retrieved {len(publications_data)} publications",
        data={"publications": publications_data},
    )
