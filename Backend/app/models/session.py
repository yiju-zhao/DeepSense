from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Many-to-many relationship table for sessions and persons (as speakers)
session_person = Table(
    "session_person",
    Base.metadata,
    Column("session_id", Integer, ForeignKey("sessions.session_id"), primary_key=True),
    Column("person_id", Integer, ForeignKey("persons.person_id"), primary_key=True),
    Column("role", String(100)),  # Role in the session: "speaker", "moderator", "panelist", etc.
)

class Session(Base):
    """
    Session model representing conference sessions.
    """
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(Integer, ForeignKey("conference_instances.instance_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    location = Column(String(255))
    session_type = Column(String(100))  # e.g., "keynote", "paper", "workshop"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with ConferenceInstance
    conference_instance = relationship("ConferenceInstance", back_populates="sessions")
    
    # Relationship with Person (many-to-many) as speakers
    speakers = relationship("Person", secondary=session_person, back_populates="speaking_sessions")

    def __repr__(self):
        return f"<Session(id={self.session_id}, title={self.title})>"