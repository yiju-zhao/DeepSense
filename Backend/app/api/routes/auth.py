from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserWithToken
from app.services.user import UserService

router = APIRouter()
user_service = UserService()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_in: UserCreate
) -> Any:
    """
    Register a new user.
    """
    # Check if user with the same email exists
    user = await user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    # Check if user with the same username exists
    user = await user_service.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists"
        )
    
    # Create new user
    user = await user_service.create(db, obj_in=user_in)
    return user


@router.post("/login", response_model=UserWithToken)
async def login(
    *,
    db: AsyncSession = Depends(get_async_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Authenticate user
    user = await user_service.authenticate(
        db, username_or_email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is active
    if not await user_service.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.user_id, expires_delta=access_token_expires
    )
    
    # Return user with token
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "roles": user.roles,
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=UserWithToken)
async def refresh_token(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Refresh access token.
    """
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.user_id, expires_delta=access_token_expires
    )
    
    # Return user with token
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "roles": current_user.roles,
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout() -> Any:
    """
    Logout user.
    
    Note: This is a placeholder endpoint. Since JWT tokens are stateless,
    the client should simply discard the token. This endpoint is provided
    for API completeness.
    """
    return {"status": "success", "message": "Logged out successfully"}