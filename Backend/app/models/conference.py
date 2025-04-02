from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base

class Conference(Base):
    """
    Conference model representing academic conferences.
    """
    __tablename__ = "conferences"

    conference_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with ConferenceInstance
    instances = relationship(
        "ConferenceInstance",
        back_populates="conference",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Database-level unique constraint
        UniqueConstraint("name", name="unique_conference_name"),
    )

    def __repr__(self):
        return f"<Conference(id={self.conference_id}, name={self.name})>"


class ConferenceInstance(Base):
    """
    ConferenceInstance model representing specific instances of conferences.
    """
    __tablename__ = "conference_instances"

    instance_id = Column(Integer, primary_key=True, autoincrement=True)
    conference_id = Column(Integer, ForeignKey("conferences.conference_id"), nullable=False)
    year = Column(Integer, nullable=False)
    location = Column(String(255))
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    website = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with Conference
    conference = relationship("Conference", back_populates="instances")
    
    # Relationship with Paper
    papers = relationship("Paper", back_populates="conference_instance", cascade="all, delete-orphan")
    
    # Relationship with Session
    sessions = relationship("Session", back_populates="conference_instance", cascade="all, delete-orphan")

    __table_args__ = (
        # Database-level unique constraint for conference_id and year
        UniqueConstraint("conference_id", "year", name="unique_conference_instance"),
    )

    def __repr__(self):
        return f"<ConferenceInstance(id={self.instance_id}, conference_id={self.conference_id}, year={self.year})>"