from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_password_hash, verify_password
from models.user import User
from repositories.user import UserRepository
from schemas.user import UserCreate, UserUpdate
from services.base import BaseService

class UserService(BaseService[User, UserCreate, UserUpdate, UserRepository]):
    """
    Service for User model with custom methods.
    """
    
    def __init__(self):
        super().__init__(UserRepository())
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: Email of the user to get
            
        Returns:
            The user if found, None otherwise
        """
        return await self.repository.get_by_email(db, email)
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: Username of the user to get
            
        Returns:
            The user if found, None otherwise
        """
        return await self.repository.get_by_username(db, username)
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password.
        
        Args:
            db: Database session
            obj_in: Input data
            
        Returns:
            The created user
        """
        # Hash the password
        hashed_password = get_password_hash(obj_in.password)
        
        # Create user data without the password
        user_data = obj_in.model_dump(exclude={"password"})
        
        # Add the hashed password
        user_data["hashed_password"] = hashed_password
        
        # Create the user
        return await super().create(db, obj_in=user_data)
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        id: int, 
        obj_in: UserUpdate
    ) -> User:
        """
        Update a user, hashing the password if provided.
        
        Args:
            db: Database session
            id: ID of the user to update
            obj_in: Input data
            
        Returns:
            The updated user
        """
        # Get the user
        user = await self.repository.get_by_id_or_404(db, id)
        
        # Convert input to dict
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Hash the password if provided
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        # Update the user
        return await self.repository.update(db, db_obj=user, obj_in=update_data)
    
    async def authenticate(
        self, 
        db: AsyncSession, 
        *, 
        username_or_email: str, 
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user.
        
        Args:
            db: Database session
            username_or_email: Username or email of the user
            password: Password to verify
            
        Returns:
            The authenticated user if successful, None otherwise
        """
        # Try to get the user by email
        user = await self.repository.get_by_email(db, username_or_email)
        
        # If not found, try by username
        if not user:
            user = await self.repository.get_by_username(db, username_or_email)
        
        # If still not found or password doesn't match, return None
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def is_active(self, user: User) -> bool:
        """
        Check if a user is active.
        
        Args:
            user: The user to check
            
        Returns:
            True if the user is active, False otherwise
        """
        return user.is_active
    
    async def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser.
        
        Args:
            user: The user to check
            
        Returns:
            True if the user is a superuser, False otherwise
        """
        return user.is_superuser
    
    async def has_role(self, user: User, role: str) -> bool:
        """
        Check if a user has a specific role.
        
        Args:
            user: The user to check
            role: The role to check for
            
        Returns:
            True if the user has the role, False otherwise
        """
        if not user.roles:
            return False
        
        roles = user.roles.split(",")
        return role in roles
    
    async def get_users_by_role(self, db: AsyncSession, role: str) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            db: Database session
            role: Role to filter by
            
        Returns:
            List of users with the specified role
        """
        return await self.repository.get_users_by_role(db, role)