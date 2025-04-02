from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conference import Conference, ConferenceInstance
from app.repositories.base import BaseRepository
from app.schemas.conference import ConferenceCreate, ConferenceUpdate, ConferenceInstanceCreate, ConferenceInstanceUpdate


class ConferenceRepository(BaseRepository[Conference, ConferenceCreate, ConferenceUpdate]):
    """
    Repository for Conference model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Conference)
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Conference]:
        """
        Get a conference by name.
        
        Args:
            db: Database session
            name: Name of the conference to get
            
        Returns:
            The conference if found, None otherwise
        """
        query = select(Conference).where(Conference.name == name)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_instances(self, db: AsyncSession, conference_id: int) -> Optional[Conference]:
        """
        Get a conference with its instances.
        
        Args:
            db: Database session
            conference_id: ID of the conference to get
            
        Returns:
            The conference with instances if found, None otherwise
        """
        query = select(Conference).where(Conference.conference_id == conference_id)
        result = await db.execute(query)
        conference = result.scalars().first()
        
        if conference:
            # Load instances
            await db.refresh(conference, ["instances"])
            
        return conference


class ConferenceInstanceRepository(BaseRepository[ConferenceInstance, ConferenceInstanceCreate, ConferenceInstanceUpdate]):
    """
    Repository for ConferenceInstance model with custom methods.
    """
    
    def __init__(self):
        super().__init__(ConferenceInstance)
    
    async def get_by_conference_and_year(
        self, 
        db: AsyncSession, 
        conference_id: int, 
        year: int
    ) -> Optional[ConferenceInstance]:
        """
        Get a conference instance by conference ID and year.
        
        Args:
            db: Database session
            conference_id: ID of the conference
            year: Year of the instance
            
        Returns:
            The conference instance if found, None otherwise
        """
        query = select(ConferenceInstance).where(
            ConferenceInstance.conference_id == conference_id,
            ConferenceInstance.year == year
        )
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_instances_by_conference(
        self, 
        db: AsyncSession, 
        conference_id: int
    ) -> List[ConferenceInstance]:
        """
        Get all instances for a conference.
        
        Args:
            db: Database session
            conference_id: ID of the conference
            
        Returns:
            List of conference instances
        """
        query = select(ConferenceInstance).where(
            ConferenceInstance.conference_id == conference_id
        ).order_by(ConferenceInstance.year.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_papers_and_sessions(
        self, 
        db: AsyncSession, 
        instance_id: int
    ) -> Optional[ConferenceInstance]:
        """
        Get a conference instance with its papers and sessions.
        
        Args:
            db: Database session
            instance_id: ID of the instance to get
            
        Returns:
            The conference instance with papers and sessions if found, None otherwise
        """
        query = select(ConferenceInstance).where(ConferenceInstance.instance_id == instance_id)
        result = await db.execute(query)
        instance = result.scalars().first()
        
        if instance:
            # Load papers and sessions
            await db.refresh(instance, ["papers", "sessions"])
            
        return instance