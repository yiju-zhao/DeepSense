from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import random
from pathlib import Path

app = FastAPI(
    title="DeepSight API",
    description="API for DeepSight technical insight tool",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class Conference(BaseModel):
    id: str
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

class ChatMessage(BaseModel):
    message: str
    response: str

# Dummy data
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
    Conference(
        id="2",
        name='FSE',
        logo='/assets/img/conference/FSE.svg',
        description='FSE description.',
        totalPapers=4200,
        averageCitation=23.8,
        yearRange='1993-2024',
        rank=2,
        impactScore=9.2,
        acceptanceRate='25-30%',
        submissionDeadline='2024-05-15',
        notificationDate='2024-07-20',
        conferenceDate='2024-11-15'
    ),
    Conference(
        id="3",
        name='ASE',
        logo='/assets/img/conference/ASE.svg',
        description='ASE description.',
        totalPapers=3800,
        averageCitation=22.1,
        yearRange='1986-2024',
        rank=3,
        impactScore=8.9,
        acceptanceRate='25-30%',
        submissionDeadline='2024-04-15',
        notificationDate='2024-06-20',
        conferenceDate='2024-09-15'
    ),
    Conference(
        id="4",
        name='ISSTA',
        logo='/assets/img/conference/ISSTA.svg',
        description='ISSTA description.',
        totalPapers=3200,
        averageCitation=20.2,
        yearRange='1989-2024',
        rank=4,
        impactScore=8.5,
        acceptanceRate='25-30%',
        submissionDeadline='2024-02-15',
        notificationDate='2024-04-20',
        conferenceDate='2024-07-15'
    ),
    Conference(
        id="5",
        name='ICSME',
        logo='/assets/img/conference/ICSME.svg',
        description='ICSME description.',
        totalPapers=3500,
        averageCitation=21.5,
        yearRange='1983-2024',
        rank=5,
        impactScore=8.3,
        acceptanceRate='30-35%',
        submissionDeadline='2024-03-15',
        notificationDate='2024-05-20',
        conferenceDate='2024-08-15'
    )
]

DUMMY_ORGANIZATIONS = [
    Organization(
        id="1",
        name="Stanford University",
        description="Leading research university in AI and ML",
        total_papers=200,
        conferences=["NeurIPS", "ICML"]
    ),
    Organization(
        id="2",
        name="MIT",
        description="Massachusetts Institute of Technology",
        total_papers=180,
        conferences=["NeurIPS", "ICML"]
    ),
]

DUMMY_PAPERS = [
    Paper(
        id="1",
        title="Large Language Models in Scientific Discovery",
        authors=["John Smith", "Mary Brown"],
        conference="NeurIPS",
        year=2024,
        abstract="This paper explores the application of large language models in scientific research...",
        keywords=["LLM", "Scientific Discovery", "AI"],
        citations=45,
        organization="Stanford University"
    ),
    Paper(
        id="2",
        title="Neural Network Architecture Search",
        authors=["Rachel Williams"],
        conference="ICML",
        year=2023,
        abstract="A novel approach to automated neural architecture search...",
        keywords=["Neural Architecture", "AutoML", "Optimization"],
        citations=89,
        organization="MIT"
    ),
    Paper(
        id="3",
        title="Cooperative Hardware - Prompt Learning for Snapshot Compressive Imaging",
        authors=["Jiamian Wang", "Zongliang Wu", "Yulun Zhang", "Xin Yuan", "Tao Lin", "ZHIQIANG TAO"],
        conference="NeurIPS",
        year=2024,
        abstract="This paper explores the application of cooperative hardware in scientific research...",
        keywords=["Cooperative Hardware", "Prompt Learning", "Snapshot Compressive Imaging"],
        citations=100,
        organization="University of Toronto"
    ),
    Paper(
        id="4",
        title="PERIA: Perceive, Reason, Imagine, Act via Holistic Language and Vision Planning for Manipulation",
        authors=["Fei Ni", "Jianye HAO", "Shiguang Wu", "Longxin Kou", "Yifu Yuan", "Zibin Dong", "Jinyi Liu", "MingZhi Li", "Yuzheng Zhuang", "YAN ZHENG"],
        conference="NeurIPS",
        year=2024,
        abstract="This paper explores the application of cooperative hardware in scientific research...",
        keywords=["Perceive, Reason, Imagine, Act via Holistic Language and Vision Planning for Manipulation"],
        citations=100,
        organization="University of Pennsylvania"
    ),
    Paper(
        id="5",
        title="How We Design Tools for Technical Insight Team",
        authors=["Yuhe Chen", "Eason Zhao", "Jiwen Yu"],
        conference="NeurIPS",
        year=2025,
        abstract="This paper discusses the design and implementation of tools for technical insight teams...",
        keywords=["LLM, Tools, Technical Insight"],
        citations=0,
        organization="University of Toronto"
    )
]

# API Routes
@app.get("/")
async def root():
    return {"message": "Welcome to DeepSight API"}

@app.get("/api/v1/conferences", response_model=List[Conference])
async def get_conferences():
    return DUMMY_CONFERENCES

@app.get("/api/v1/conferences/{conference_id}", response_model=Conference)
async def get_conference(conference_id: str):
    conference = next((c for c in DUMMY_CONFERENCES if c.id == conference_id), None)
    if not conference:
        raise HTTPException(status_code=404, detail="Conference not found")
    return conference

@app.get("/api/v1/organizations", response_model=List[Organization])
async def get_organizations():
    return DUMMY_ORGANIZATIONS

@app.get("/api/v1/organizations/{organization_id}", response_model=Organization)
async def get_organization(organization_id: str):
    organization = next((o for o in DUMMY_ORGANIZATIONS if o.id == organization_id), None)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

@app.get("/api/v1/papers", response_model=List[Paper])
async def get_papers(
    conference: Optional[str] = None,
    year: Optional[int] = None,
    organization: Optional[str] = None,
    keyword: Optional[str] = None
):
    filtered_papers = DUMMY_PAPERS
    
    if conference:
        filtered_papers = [p for p in filtered_papers if p.conference == conference]
    if year:
        filtered_papers = [p for p in filtered_papers if p.year == year]
    if organization:
        filtered_papers = [p for p in filtered_papers if p.organization == organization]
    if keyword:
        filtered_papers = [p for p in filtered_papers if keyword.lower() in [k.lower() for k in p.keywords]]
    
    return filtered_papers

@app.get("/api/v1/papers/{paper_id}", response_model=Paper)
async def get_paper(paper_id: str):
    paper = next((p for p in DUMMY_PAPERS if p.id == paper_id), None)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@app.get("/api/v1/analytics/conference-stats")
async def get_conference_stats():
    return {
        "total_conferences": len(DUMMY_CONFERENCES),
        "total_papers": sum(c.totalPapers for c in DUMMY_CONFERENCES),
        "years_covered": sum(int(c.yearRange.split('-')[1]) - int(c.yearRange.split('-')[0]) for c in DUMMY_CONFERENCES),
        "avg_papers_per_year": sum(c.totalPapers for c in DUMMY_CONFERENCES) / len(DUMMY_CONFERENCES)
    }

@app.get("/api/v1/analytics/organization-stats")
async def get_organization_stats():
    return {
        "total_organizations": len(DUMMY_ORGANIZATIONS),
        "total_papers": sum(o.total_papers for o in DUMMY_ORGANIZATIONS),
        "organizations_by_conference": {
            conf: len([o for o in DUMMY_ORGANIZATIONS if conf in o.conferences])
            for conf in set(conf for o in DUMMY_ORGANIZATIONS for conf in o.conferences)
        }
    }

@app.post("/api/v1/chat", response_model=ChatMessage)
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

@app.get("/api/v1/audio")
async def get_audio():
    # For demo purposes, we'll serve a static audio file
    audio_path = Path(__file__).parent.parent / "Frontend/public/assets/audio/new-divide.mp3"
    
    if not audio_path.exists():
        return Response(content="Audio file not found", status_code=404)
        
    audio_bytes = audio_path.read_bytes()
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "Accept-Ranges": "bytes",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 