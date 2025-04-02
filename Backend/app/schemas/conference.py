from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConferenceBase(BaseModel):
    """Base schema for Conference."""
    name: str
    type: Optional[str] = None
    description: Optional[str] = None


class ConferenceCreate(ConferenceBase):
    """Schema for creating a Conference."""
    pass


class ConferenceUpdate(ConferenceBase):
    """Schema for updating a Conference."""
    name: Optional[str] = None


class ConferenceInDBBase(ConferenceBase):
    """Base schema for Conference in DB."""
    conference_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Conference(ConferenceInDBBase):
    """Schema for Conference response."""
    pass


class ConferenceWithInstances(Conference):
    """Schema for Conference with instances."""
    instances: List["ConferenceInstance"] = []


class ConferenceInstanceBase(BaseModel):
    """Base schema for ConferenceInstance."""
    conference_id: int
    year: int
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    website: Optional[str] = None


class ConferenceInstanceCreate(ConferenceInstanceBase):
    """Schema for creating a ConferenceInstance."""
    pass


class ConferenceInstanceUpdate(ConferenceInstanceBase):
    """Schema for updating a ConferenceInstance."""
    conference_id: Optional[int] = None
    year: Optional[int] = None


class ConferenceInstanceInDBBase(ConferenceInstanceBase):
    """Base schema for ConferenceInstance in DB."""
    instance_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConferenceInstance(ConferenceInstanceInDBBase):
    """Schema for ConferenceInstance response."""
    pass


class ConferenceInstanceWithDetails(ConferenceInstance):
    """Schema for ConferenceInstance with details."""
    conference: Conference
    paper_count: Optional[int] = None
    session_count: Optional[int] = None


# Update forward references
ConferenceWithInstances.update_forward_refs()