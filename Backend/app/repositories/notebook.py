from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import Notebook, NotebookSnapshot
from app.repositories.base import BaseRepository
from app.schemas.report import NotebookCreate, NotebookUpdate


class NotebookRepository(BaseRepository[Notebook, NotebookCreate, NotebookUpdate]):
    """
    Repository for Notebook model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Notebook)
    
    async def get_by_title(self, db: AsyncSession, title: str) -> Optional[Notebook]:
        """
        Get a notebook by title.
        
        Args:
            db: Database session
            title: Title of the notebook to get
            
        Returns:
            The notebook if found, None otherwise
        """
        query = select(Notebook).where(func.lower(Notebook.title) == func.lower(title))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_notebooks_by_user(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[Notebook]:
        """
        Get all notebooks for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of notebooks
        """
        query = select(Notebook).where(
            Notebook.user_id == user_id
        ).order_by(Notebook.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_notebooks_by_instance(
        self, 
        db: AsyncSession, 
        instance_id: int
    ) -> List[Notebook]:
        """
        Get all notebooks for a conference instance.
        
        Args:
            db: Database session
            instance_id: ID of the conference instance
            
        Returns:
            List of notebooks
        """
        query = select(Notebook).where(
            Notebook.instance_id == instance_id
        ).order_by(Notebook.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_public_notebooks(
        self, 
        db: AsyncSession
    ) -> List[Notebook]:
        """
        Get all public notebooks.
        
        Args:
            db: Database session
            
        Returns:
            List of public notebooks
        """
        query = select(Notebook).where(
            Notebook.is_public == True
        ).order_by(Notebook.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_snapshots(
        self, 
        db: AsyncSession, 
        notebook_id: int
    ) -> Optional[Notebook]:
        """
        Get a notebook with its snapshots.
        
        Args:
            db: Database session
            notebook_id: ID of the notebook to get
            
        Returns:
            The notebook with snapshots if found, None otherwise
        """
        query = select(Notebook).options(
            selectinload(Notebook.snapshots)
        ).where(Notebook.notebook_id == notebook_id)
        result = await db.execute(query)
        return result.scalars().first()


class NotebookSnapshotRepository(BaseRepository[NotebookSnapshot, None, None]):
    """
    Repository for NotebookSnapshot model with custom methods.
    """
    
    def __init__(self):
        super().__init__(NotebookSnapshot)
    
    async def get_snapshots_by_notebook(
        self, 
        db: AsyncSession, 
        notebook_id: int
    ) -> List[NotebookSnapshot]:
        """
        Get all snapshots for a notebook.
        
        Args:
            db: Database session
            notebook_id: ID of the notebook
            
        Returns:
            List of notebook snapshots
        """
        query = select(NotebookSnapshot).where(
            NotebookSnapshot.notebook_id == notebook_id
        ).order_by(NotebookSnapshot.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_latest_snapshot(
        self, 
        db: AsyncSession, 
        notebook_id: int
    ) -> Optional[NotebookSnapshot]:
        """
        Get the latest snapshot for a notebook.
        
        Args:
            db: Database session
            notebook_id: ID of the notebook
            
        Returns:
            The latest notebook snapshot if found, None otherwise
        """
        query = select(NotebookSnapshot).where(
            NotebookSnapshot.notebook_id == notebook_id
        ).order_by(NotebookSnapshot.created_at.desc()).limit(1)
        result = await db.execute(query)
        return result.scalars().first()