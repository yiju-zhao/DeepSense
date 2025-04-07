from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base

class User(Base):
    """
    User model for authentication and authorization.
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Define roles as a string column that stores comma-separated roles
    roles = Column(String, default="user")  # e.g., "user,editor,admin"
    
    def __repr__(self):
        return f"<User(id={self.user_id}, username={self.username})>"