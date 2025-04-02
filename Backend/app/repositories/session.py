from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import Session
from app.repositories.base import BaseRepository
from app.schemas.session import SessionCreate, SessionUpdate


class SessionRepository(BaseRepository[Session, SessionCreate, SessionUpdate]):
    """
    Repository for Session model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Session)
    
    async def get_by_title(self, db: AsyncSession, title: str) -> Optional[Session]:
        """
        Get a session by title.
        
        Args:
            db: Database session
            title: Title of the session to get
            
        Returns:
            The session if found, None otherwise
        """
        query = select(Session).where(func.lower(Session.title) == func.lower(title))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_sessions_by_instance(
        self, 
        db: AsyncSession, 
        instance_id: int
    ) -> List[Session]:
        """
        Get all sessions for a conference instance.
        
        Args:
            db: Database session
            instance_id: ID of the conference instance
            
        Returns:
            List of sessions
        """
        query = select(Session).where(
            Session.instance_id == instance_id
        ).order_by(Session.start_time)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_sessions_by_type(
        self, 
        db: AsyncSession, 
        session_type: str
    ) -> List[Session]:
        """
        Get all sessions of a specific type.
        
        Args:
            db: Database session
            session_type: Type of session to filter by
            
        Returns:
            List of sessions
        """
        query = select(Session).where(
            func.lower(Session.session_type) == func.lower(session_type)
        ).order_by(Session.start_time)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_speakers(
        self, 
        db: AsyncSession, 
        session_id: int
    ) -> Optional[Session]:
        """
        Get a session with its speakers.
        
        Args:
            db: Database session
            session_id: ID of the session to get
            
        Returns:
            The session with speakers if found, None otherwise
        """
        query = select(Session).options(
            selectinload(Session.speakers)
        ).where(Session.session_id == session_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_all_relations(
        self, 
        db: AsyncSession, 
        session_id: int
    ) -> Optional[Session]:
        """
        Get a session with all its relations (speakers, conference instance).
        
        Args:
            db: Database session
            session_id: ID of the session to get
            
        Returns:
            The session with all relations if found, None otherwise
        """
        query = select(Session).options(
            selectinload(Session.speakers),
            selectinload(Session.conference_instance)
        ).where(Session.session_id == session_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_sessions_by_speaker(
        self, 
        db: AsyncSession, 
        person_id: int
    ) -> List[Session]:
        """
        Get all sessions for a specific speaker.
        
        Args:
            db: Database session
            person_id: ID of the person (speaker)
            
        Returns:
            List of sessions
        """
        query = select(Session).join(
            Session.speakers
        ).where(
            Session.speakers.any(person_id=person_id)
        ).order_by(Session.start_time)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_sessions_by_date_range(
        self, 
        db: AsyncSession, 
        start_date: str,
        end_date: str
    ) -> List[Session]:
        """
        Get all sessions within a date range.
        
        Args:
            db: Database session
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of sessions
        """
        query = select(Session).where(
            Session.start_time >= start_date,
            Session.end_time <= end_date
        ).order_by(Session.start_time)
        result = await db.execute(query)
        return result.scalars().all()