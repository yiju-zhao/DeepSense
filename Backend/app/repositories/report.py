from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import Report, ReportVersion
from app.repositories.base import BaseRepository
from app.schemas.report import ReportCreate, ReportUpdate


class ReportRepository(BaseRepository[Report, ReportCreate, ReportUpdate]):
    """
    Repository for Report model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Report)
    
    async def get_by_title(self, db: AsyncSession, title: str) -> Optional[Report]:
        """
        Get a report by title.
        
        Args:
            db: Database session
            title: Title of the report to get
            
        Returns:
            The report if found, None otherwise
        """
        query = select(Report).where(func.lower(Report.title) == func.lower(title))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_reports_by_user(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[Report]:
        """
        Get all reports for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of reports
        """
        query = select(Report).where(
            Report.user_id == user_id
        ).order_by(Report.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_reports_by_instance(
        self, 
        db: AsyncSession, 
        instance_id: int
    ) -> List[Report]:
        """
        Get all reports for a conference instance.
        
        Args:
            db: Database session
            instance_id: ID of the conference instance
            
        Returns:
            List of reports
        """
        query = select(Report).where(
            Report.instance_id == instance_id
        ).order_by(Report.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_public_reports(
        self, 
        db: AsyncSession
    ) -> List[Report]:
        """
        Get all public reports.
        
        Args:
            db: Database session
            
        Returns:
            List of public reports
        """
        query = select(Report).where(
            Report.is_public == True
        ).order_by(Report.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_versions(
        self, 
        db: AsyncSession, 
        report_id: int
    ) -> Optional[Report]:
        """
        Get a report with its versions.
        
        Args:
            db: Database session
            report_id: ID of the report to get
            
        Returns:
            The report with versions if found, None otherwise
        """
        query = select(Report).options(
            selectinload(Report.versions)
        ).where(Report.report_id == report_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_papers(
        self, 
        db: AsyncSession, 
        report_id: int
    ) -> Optional[Report]:
        """
        Get a report with its related papers.
        
        Args:
            db: Database session
            report_id: ID of the report to get
            
        Returns:
            The report with papers if found, None otherwise
        """
        query = select(Report).options(
            selectinload(Report.papers)
        ).where(Report.report_id == report_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_all_relations(
        self, 
        db: AsyncSession, 
        report_id: int
    ) -> Optional[Report]:
        """
        Get a report with all its relations (versions, papers, shared users).
        
        Args:
            db: Database session
            report_id: ID of the report to get
            
        Returns:
            The report with all relations if found, None otherwise
        """
        query = select(Report).options(
            selectinload(Report.versions),
            selectinload(Report.papers),
            selectinload(Report.shared_with),
            selectinload(Report.conference_instance)
        ).where(Report.report_id == report_id)
        result = await db.execute(query)
        return result.scalars().first()


class ReportVersionRepository(BaseRepository[ReportVersion, None, None]):
    """
    Repository for ReportVersion model with custom methods.
    """
    
    def __init__(self):
        super().__init__(ReportVersion)
    
    async def get_versions_by_report(
        self, 
        db: AsyncSession, 
        report_id: int
    ) -> List[ReportVersion]:
        """
        Get all versions for a report.
        
        Args:
            db: Database session
            report_id: ID of the report
            
        Returns:
            List of report versions
        """
        query = select(ReportVersion).where(
            ReportVersion.report_id == report_id
        ).order_by(ReportVersion.version_number.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_latest_version(
        self, 
        db: AsyncSession, 
        report_id: int
    ) -> Optional[ReportVersion]:
        """
        Get the latest version for a report.
        
        Args:
            db: Database session
            report_id: ID of the report
            
        Returns:
            The latest report version if found, None otherwise
        """
        query = select(ReportVersion).where(
            ReportVersion.report_id == report_id
        ).order_by(ReportVersion.version_number.desc()).limit(1)
        result = await db.execute(query)
        return result.scalars().first()