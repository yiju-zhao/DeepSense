from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import Base
from repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]):
    """
    Base service class with default CRUD operations.
    """

    def __init__(self, repository: RepositoryType):
        """
        Initialize the service with a repository.
        
        Args:
            repository: The repository instance
        """
        self.repository = repository

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            db: Database session
            id: ID of the record to get
            
        Returns:
            The record if found, None otherwise
        """
        return await self.repository.get(db, id)

    async def get_by_id_or_404(self, db: AsyncSession, id: Any, detail: str = None) -> ModelType:
        """
        Get a record by ID or raise a 404 exception.
        
        Args:
            db: Database session
            id: ID of the record to get
            detail: Optional detail message for the exception
            
        Returns:
            The record if found
            
        Raises:
            NotFoundException: If the record is not found
        """
        return await self.repository.get_by_id_or_404(db, id, detail)

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dictionary of filters
            
        Returns:
            List of records
        """
        return await self.repository.get_multi(db, skip=skip, limit=limit, filters=filters)

    async def create(self, db: AsyncSession, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Input data
            
        Returns:
            The created record
        """
        return await self.repository.create(db, obj_in=obj_in)

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        id: Any, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: Database session
            id: ID of the record to update
            obj_in: Input data
            
        Returns:
            The updated record
            
        Raises:
            NotFoundException: If the record is not found
        """
        db_obj = await self.repository.get_by_id_or_404(db, id)
        return await self.repository.update(db, db_obj=db_obj, obj_in=obj_in)

    async def delete(self, db: AsyncSession, *, id: Any) -> ModelType:
        """
        Delete a record.
        
        Args:
            db: Database session
            id: ID of the record to delete
            
        Returns:
            The deleted record
            
        Raises:
            NotFoundException: If the record is not found
        """
        return await self.repository.delete(db, id=id)

    async def count(self, db: AsyncSession, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            db: Database session
            filters: Optional dictionary of filters
            
        Returns:
            Number of records
        """
        return await self.repository.count(db, filters=filters)