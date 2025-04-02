from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Many-to-many relationship tables
paper_person = Table(
    "paper_person",
    Base.metadata,
    Column("paper_id", Integer, ForeignKey("papers.paper_id"), primary_key=True),
    Column("person_id", Integer, ForeignKey("persons.person_id"), primary_key=True),
    Column("is_corresponding", Boolean, default=False),  # Flag for corresponding author
    Column("author_order", Integer),  # Order of authors in the paper
)

paper_keyword = Table(
    "paper_keyword",
    Base.metadata,
    Column("paper_id", Integer, ForeignKey("papers.paper_id"), primary_key=True),
    Column("keyword_id", Integer, ForeignKey("keywords.keyword_id"), primary_key=True),
)

class Paper(Base):
    """
    Paper model representing academic papers.
    """
    __tablename__ = "papers"

    paper_id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(Integer, ForeignKey("conference_instances.instance_id"), nullable=False)
    title = Column(String(255), nullable=False)
    abstract = Column(Text)
    pdf_url = Column(String(255))
    doi = Column(String(100))
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with ConferenceInstance
    conference_instance = relationship("ConferenceInstance", back_populates="papers")
    
    # Relationship with Person (many-to-many)
    authors = relationship("Person", secondary=paper_person, back_populates="authored_papers")
    
    # Relationship with Keyword (many-to-many)
    keywords = relationship("Keyword", secondary=paper_keyword, back_populates="papers")
    
    # Relationship with Reference
    references = relationship("Reference", back_populates="paper", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Paper(id={self.paper_id}, title={self.title})>"


class Person(Base):
    """
    Person model representing both paper authors and session speakers.
    """
    __tablename__ = "persons"

    person_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    bio = Column(Text)
    website = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with Paper (many-to-many) as author
    authored_papers = relationship("Paper", secondary=paper_person, back_populates="authors")
    
    # Relationship with Session (many-to-many) as speaker
    speaking_sessions = relationship("Session", secondary="session_person", back_populates="speakers")
    
    # Relationship with Organization
    organizations = relationship("Organization", back_populates="person", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Person(id={self.person_id}, name={self.name})>"


class Organization(Base):
    """
    Organization model representing institutions that people are affiliated with.
    """
    __tablename__ = "organizations"

    organization_id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=False)
    name = Column(String(255), nullable=False)
    department = Column(String(255))
    country = Column(String(100))
    website = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with Person
    person = relationship("Person", back_populates="organizations")

    def __repr__(self):
        return f"<Affiliation(id={self.affiliation_id}, institution={self.institution})>"


class Keyword(Base):
    """
    Keyword model representing paper keywords.
    """
    __tablename__ = "keywords"

    keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with Paper (many-to-many)
    papers = relationship("Paper", secondary=paper_keyword, back_populates="keywords")

    def __repr__(self):
        return f"<Keyword(id={self.keyword_id}, name={self.name})>"


class Reference(Base):
    """
    Reference model representing paper references.
    """
    __tablename__ = "references"

    reference_id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey("papers.paper_id"), nullable=False)
    title = Column(String(255), nullable=False)
    authors = Column(String(255))
    venue = Column(String(255))
    year = Column(Integer)
    doi = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with Paper
    paper = relationship("Paper", back_populates="references")

    def __repr__(self):
        return f"<Reference(id={self.reference_id}, title={self.title})>"