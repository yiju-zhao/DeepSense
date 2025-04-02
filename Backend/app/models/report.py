from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Many-to-many relationship table for reports and papers
report_paper = Table(
    "report_paper",
    Base.metadata,
    Column("report_id", Integer, ForeignKey("reports.report_id"), primary_key=True),
    Column("paper_id", Integer, ForeignKey("papers.paper_id"), primary_key=True),
)

# Many-to-many relationship table for shared reports
report_user = Table(
    "report_user",
    Base.metadata,
    Column("report_id", Integer, ForeignKey("reports.report_id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.user_id"), primary_key=True),
    Column("permission", String(50), default="read"),  # read, edit, admin
)

class Report(Base):
    """
    Report model representing AI-generated reports.
    """
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    instance_id = Column(Integer, ForeignKey("conference_instances.instance_id"), nullable=True)
    is_public = Column(Boolean, default=False)
    metadata = Column(JSON)  # Store additional metadata as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with User (owner)
    owner = relationship("User", foreign_keys=[user_id])
    
    # Relationship with ConferenceInstance
    conference_instance = relationship("ConferenceInstance")
    
    # Relationship with Paper (many-to-many)
    papers = relationship("Paper", secondary=report_paper)
    
    # Relationship with User (shared with)
    shared_with = relationship("User", secondary=report_user)
    
    # Relationship with ReportVersion
    versions = relationship("ReportVersion", back_populates="report", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Report(id={self.report_id}, title={self.title})>"


class ReportVersion(Base):
    """
    ReportVersion model representing versions of reports.
    """
    __tablename__ = "report_versions"

    version_id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.report_id"), nullable=False)
    content = Column(Text, nullable=False)
    version_number = Column(Integer, nullable=False)
    comment = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship with Report
    report = relationship("Report", back_populates="versions")

    def __repr__(self):
        return f"<ReportVersion(id={self.version_id}, report_id={self.report_id}, version={self.version_number})>"


class Notebook(Base):
    """
    Notebook model representing interactive notebooks.
    """
    __tablename__ = "notebooks"

    notebook_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(JSON, nullable=False)  # Store notebook cells as JSON
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    instance_id = Column(Integer, ForeignKey("conference_instances.instance_id"), nullable=True)
    is_public = Column(Boolean, default=False)
    metadata = Column(JSON)  # Store additional metadata as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with User (owner)
    owner = relationship("User", foreign_keys=[user_id])
    
    # Relationship with ConferenceInstance
    conference_instance = relationship("ConferenceInstance")
    
    # Relationship with NotebookSnapshot
    snapshots = relationship("NotebookSnapshot", back_populates="notebook", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Notebook(id={self.notebook_id}, title={self.title})>"


class NotebookSnapshot(Base):
    """
    NotebookSnapshot model representing snapshots of notebooks.
    """
    __tablename__ = "notebook_snapshots"

    snapshot_id = Column(Integer, primary_key=True, autoincrement=True)
    notebook_id = Column(Integer, ForeignKey("notebooks.notebook_id"), nullable=False)
    content = Column(JSON, nullable=False)  # Store notebook cells as JSON
    snapshot_name = Column(String(255), nullable=False)
    comment = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship with Notebook
    notebook = relationship("Notebook", back_populates="snapshots")

    def __repr__(self):
        return f"<NotebookSnapshot(id={self.snapshot_id}, notebook_id={self.notebook_id}, name={self.snapshot_name})>"