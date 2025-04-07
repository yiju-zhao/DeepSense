# Backend/app/api/routes/frontend_adapter.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel
import random

# Import your existing models
from database import SessionLocal
from models.tasks import Publication, PaperScores, ArxivPaper, StandardResponse

# Create models that match what the frontend expects (based on dummy.py)
class Conference(BaseModel):
    id: str
    name: str
    logo: str
    description: str
    totalPapers: int
    averageCitation: float
    yearRange: str
    rank: int
    impactScore: float
    acceptanceRate: str
    submissionDeadline: str
    notificationDate: str
    conferenceDate: str

class Organization(BaseModel):
    id: str
    name: str
    description: str
    total_papers: int
    conferences: List[str]

class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    conference: str
    year: int
    abstract: str
    keywords: List[str]
    citations: int
    organization: str
    ai_score: Optional[float] = None
    reason: Optional[str] = None
    audience: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    response: str

# Create a router for the frontend adapter
router = APIRouter(prefix="/frontend", tags=["frontend"])

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dummy conferences (same as in dummy.py)
DUMMY_CONFERENCES = [
    Conference(
        id="1",
        name='ICSE',
        logo='/assets/img/conference/ICSE.svg',
        description='ICSE description.',
        totalPapers=5000,
        averageCitation=25.5,
        yearRange='1975-2024',
        rank=1,
        impactScore=9.8,
        acceptanceRate='20-25%',
        submissionDeadline='2024-10-15',
        notificationDate='2024-12-20',
        conferenceDate='2025-05-15'
    ),
    # Add the rest of the conferences from dummy.py
]

# Dummy organizations (same as in dummy.py)
DUMMY_ORGANIZATIONS = [
    Organization(
        id="1",
        name="Stanford University",
        description="Leading research university in AI and ML",
        total_papers=200,
        conferences=["NeurIPS", "ICML"]
    ),
    # Add the rest of the organizations from dummy.py
]

# Root endpoint
@router.get("/")
async def root():
    return {"message": "Welcome to DeepSight API Adapter"}

# Conferences endpoints
@router.get("/conferences", response_model=List[Conference])
async def get_conferences():
    return DUMMY_CONFERENCES

@router.get("/conferences/{conference_id}", response_model=Conference)
async def get_conference(conference_id: str):
    conference = next((c for c in DUMMY_CONFERENCES if c.id == conference_id), None)
    if not conference:
        raise HTTPException(status_code=404, detail="Conference not found")
    return conference

# Organizations endpoints
@router.get("/organizations", response_model=List[Organization])
async def get_organizations():
    return DUMMY_ORGANIZATIONS

@router.get("/organizations/{organization_id}", response_model=Organization)
async def get_organization(organization_id: str):
    organization = next((o for o in DUMMY_ORGANIZATIONS if o.id == organization_id), None)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

# Papers endpoints - These will use actual data from your database
@router.get("/papers", response_model=List[Paper])
async def get_papers(
    db: Session = Depends(get_db),
    conference: Optional[str] = None,
    year: Optional[int] = None,
    organization: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    # Get papers from your actual database
    query = db.query(Publication).outerjoin(PaperScores, Publication.paper_id == PaperScores.paper_id)
    
    # Apply filters if provided
    if year:
        query = query.filter(Publication.year == year)
    if keyword and keyword.strip():
        query = query.filter(Publication.keywords.contains(keyword))
    
    # Apply pagination
    publications = query.offset(skip).limit(limit).all()
    
    # Transform to the frontend's expected format
    papers = []
    for pub in publications:
        # Get corresponding arxiv paper for author information
        arxiv_paper = db.query(ArxivPaper).filter(ArxivPaper.arxiv_id == pub.paper_id).first()
        authors = arxiv_paper.authors if arxiv_paper and arxiv_paper.authors else []
        
        # Convert keywords from comma-separated string to list
        keywords_list = [k.strip() for k in pub.keywords.split(',')] if pub.keywords else []
        
        # Create paper object
        paper = Paper(
            id=pub.paper_id,
            title=pub.title,
            authors=authors,
            conference=conference or "Unknown",  # Default to "Unknown" if not specified
            year=pub.year or (pub.publish_date.year if pub.publish_date else datetime.now().year),
            abstract=pub.abstract or "",
            keywords=keywords_list,
            citations=pub.citation_count or 0,
            organization=organization or "Unknown",  # Default to "Unknown" if not specified
            ai_score=pub.scores.weighted_score if pub.scores else None,
            reason=pub.scores.recommend_reason if pub.scores and pub.scores.recommend else None,
            audience=pub.scores.who_should_read if pub.scores else None
        )
        papers.append(paper)
    
    return papers

@router.get("/papers/{paper_id}", response_model=Paper)
async def get_paper(paper_id: str, db: Session = Depends(get_db)):
    # Get the paper from your actual database
    publication = db.query(Publication).filter(Publication.paper_id == paper_id).first()
    if not publication:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get corresponding arxiv paper for author information
    arxiv_paper = db.query(ArxivPaper).filter(ArxivPaper.arxiv_id == paper_id).first()
    authors = arxiv_paper.authors if arxiv_paper and arxiv_paper.authors else []
    
    # Convert keywords from comma-separated string to list
    keywords_list = [k.strip() for k in publication.keywords.split(',')] if publication.keywords else []
    
    # Get scores
    scores = db.query(PaperScores).filter(PaperScores.paper_id == paper_id).first()
    
    # Create paper object
    paper = Paper(
        id=publication.paper_id,
        title=publication.title,
        authors=authors,
        conference="Unknown",  # Default since we don't know the conference
        year=publication.year or (publication.publish_date.year if publication.publish_date else datetime.now().year),
        abstract=publication.abstract or "",
        keywords=keywords_list,
        citations=publication.citation_count or 0,
        organization="Unknown",  # Default since we don't know the organization
        ai_score=scores.weighted_score if scores else None,
        reason=scores.recommend_reason if scores and scores.recommend else None,
        audience=scores.who_should_read if scores else None
    )
    
    return paper

# Analytics endpoints
@router.get("/analytics/conference-stats")
async def get_conference_stats():
    return {
        "total_conferences": len(DUMMY_CONFERENCES),
        "total_papers": sum(c.totalPapers for c in DUMMY_CONFERENCES),
        "years_covered": sum(int(c.yearRange.split('-')[1]) - int(c.yearRange.split('-')[0]) for c in DUMMY_CONFERENCES),
        "avg_papers_per_year": sum(c.totalPapers for c in DUMMY_CONFERENCES) / len(DUMMY_CONFERENCES)
    }

@router.get("/analytics/organization-stats")
async def get_organization_stats():
    return {
        "total_organizations": len(DUMMY_ORGANIZATIONS),
        "total_papers": sum(o.total_papers for o in DUMMY_ORGANIZATIONS),
        "organizations_by_conference": {
            conf: len([o for o in DUMMY_ORGANIZATIONS if conf in o.conferences])
            for conf in set(conf for o in DUMMY_ORGANIZATIONS for conf in o.conferences)
        }
    }

# Chat endpoint
@router.post("/chat", response_model=ChatMessage)
async def chat(message: ChatMessage):
    # Dummy responses based on keywords in the message
    responses = [
        "Based on the paper's methodology, this approach shows promising results in improving model performance.",
        "The authors demonstrate significant improvements over baseline methods, achieving a 15% increase in accuracy.",
        "This research builds upon previous work in the field, particularly citing developments in transformer architectures.",
        "The key innovation appears to be their novel architecture design, which reduces computational complexity.",
        "According to the experimental results, the proposed method outperforms existing solutions in both efficiency and accuracy."
    ]

    return ChatMessage(
        message=message.message,
        response=random.choice(responses)
    )