from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.paper import Paper, Keyword, Reference
from app.repositories.base import BaseRepository
from app.schemas.paper import PaperCreate, PaperUpdate


class PaperRepository(BaseRepository[Paper, PaperCreate, PaperUpdate]):
    """
    Repository for Paper model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Paper)
    
    async def get_by_title(self, db: AsyncSession, title: str) -> Optional[Paper]:
        """
        Get a paper by title.
        
        Args:
            db: Database session
            title: Title of the paper to get
            
        Returns:
            The paper if found, None otherwise
        """
        query = select(Paper).where(func.lower(Paper.title) == func.lower(title))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_doi(self, db: AsyncSession, doi: str) -> Optional[Paper]:
        """
        Get a paper by DOI.
        
        Args:
            db: Database session
            doi: DOI of the paper to get
            
        Returns:
            The paper if found, None otherwise
        """
        query = select(Paper).where(Paper.doi == doi)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_papers_by_instance(
        self, 
        db: AsyncSession, 
        instance_id: int
    ) -> List[Paper]:
        """
        Get all papers for a conference instance.
        
        Args:
            db: Database session
            instance_id: ID of the conference instance
            
        Returns:
            List of papers
        """
        query = select(Paper).where(
            Paper.instance_id == instance_id
        ).order_by(Paper.title)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_papers_by_keyword(
        self, 
        db: AsyncSession, 
        keyword: str
    ) -> List[Paper]:
        """
        Get all papers with a specific keyword.
        
        Args:
            db: Database session
            keyword: Keyword to filter by
            
        Returns:
            List of papers
        """
        query = select(Paper).join(
            Paper.keywords
        ).where(
            func.lower(Keyword.name) == func.lower(keyword)
        ).order_by(Paper.title)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_authors_and_keywords(
        self, 
        db: AsyncSession, 
        paper_id: int
    ) -> Optional[Paper]:
        """
        Get a paper with its authors and keywords.
        
        Args:
            db: Database session
            paper_id: ID of the paper to get
            
        Returns:
            The paper with authors and keywords if found, None otherwise
        """
        query = select(Paper).options(
            selectinload(Paper.authors),
            selectinload(Paper.keywords)
        ).where(Paper.paper_id == paper_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_all_relations(
        self, 
        db: AsyncSession, 
        paper_id: int
    ) -> Optional[Paper]:
        """
        Get a paper with all its relations (authors, keywords, references).
        
        Args:
            db: Database session
            paper_id: ID of the paper to get
            
        Returns:
            The paper with all relations if found, None otherwise
        """
        query = select(Paper).options(
            selectinload(Paper.authors),
            selectinload(Paper.keywords),
            selectinload(Paper.references),
            selectinload(Paper.conference_instance)
        ).where(Paper.paper_id == paper_id)
        result = await db.execute(query)
        return result.scalars().first()


class KeywordRepository(BaseRepository[Keyword, None, None]):
    """
    Repository for Keyword model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Keyword)
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Keyword]:
        """
        Get a keyword by name.
        
        Args:
            db: Database session
            name: Name of the keyword to get
            
        Returns:
            The keyword if found, None otherwise
        """
        query = select(Keyword).where(func.lower(Keyword.name) == func.lower(name))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_or_create(self, db: AsyncSession, name: str) -> Keyword:
        """
        Get a keyword by name or create it if it doesn't exist.
        
        Args:
            db: Database session
            name: Name of the keyword
            
        Returns:
            The existing or newly created keyword
        """
        keyword = await self.get_by_name(db, name)
        
        if not keyword:
            keyword = Keyword(name=name)
            db.add(keyword)
            await db.commit()
            await db.refresh(keyword)
            
        return keyword
    
    async def get_popular_keywords(
        self, 
        db: AsyncSession, 
        limit: int = 20
    ) -> List[Keyword]:
        """
        Get the most popular keywords based on the number of papers.
        
        Args:
            db: Database session
            limit: Maximum number of keywords to return
            
        Returns:
            List of popular keywords
        """
        # This query counts the number of papers for each keyword and orders by count
        query = select(Keyword, func.count(Paper.paper_id).label("paper_count")).join(
            Keyword.papers
        ).group_by(
            Keyword.keyword_id
        ).order_by(
            func.count(Paper.paper_id).desc()
        ).limit(limit)
        
        result = await db.execute(query)
        return [row[0] for row in result.all()]  # Extract just the Keyword objects


class ReferenceRepository(BaseRepository[Reference, None, None]):
    """
    Repository for Reference model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Reference)
    
    async def get_references_by_paper(
        self, 
        db: AsyncSession, 
        paper_id: int
    ) -> List[Reference]:
        """
        Get all references for a paper.
        
        Args:
            db: Database session
            paper_id: ID of the paper
            
        Returns:
            List of references
        """
        query = select(Reference).where(
            Reference.paper_id == paper_id
        ).order_by(Reference.title)
        result = await db.execute(query)
        return result.scalars().all()