from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for User model with custom methods.
    """
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: Email of the user to get
            
        Returns:
            The user if found, None otherwise
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: Username of the user to get
            
        Returns:
            The user if found, None otherwise
        """
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_users_by_role(self, db: AsyncSession, role: str) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            db: Database session
            role: Role to filter by
            
        Returns:
            List of users with the specified role
        """
        # Since roles are stored as a comma-separated string, we need to use LIKE
        query = select(User).where(User.roles.like(f"%{role}%"))
        result = await db.execute(query)
        return result.scalars().all()