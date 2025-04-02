from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base schema for User."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    roles: Optional[str] = "user"


class UserCreate(UserBase):
    """Schema for creating a User."""
    username: str
    email: EmailStr
    password: str
    
    @validator("password")
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserUpdate(UserBase):
    """Schema for updating a User."""
    password: Optional[str] = None
    
    @validator("password")
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserInDBBase(UserBase):
    """Base schema for User in DB."""
    user_id: int
    
    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Schema for User response."""
    pass


class UserWithToken(User):
    """Schema for User with access token."""
    access_token: str
    token_type: str = "bearer"