from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.paper import Person, Organization
from app.repositories.base import BaseRepository


class PersonRepository(BaseRepository[Person, None, None]):
    """
    Repository for Person model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Person)
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Person]:
        """
        Get a person by name.
        
        Args:
            db: Database session
            name: Name of the person to get
            
        Returns:
            The person if found, None otherwise
        """
        query = select(Person).where(func.lower(Person.name) == func.lower(name))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Person]:
        """
        Get a person by email.
        
        Args:
            db: Database session
            email: Email of the person to get
            
        Returns:
            The person if found, None otherwise
        """
        query = select(Person).where(Person.email == email)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_papers(
        self, 
        db: AsyncSession, 
        person_id: int
    ) -> Optional[Person]:
        """
        Get a person with their papers.
        
        Args:
            db: Database session
            person_id: ID of the person to get
            
        Returns:
            The person with papers if found, None otherwise
        """
        query = select(Person).options(
            selectinload(Person.authored_papers)
        ).where(Person.person_id == person_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_organizations(
        self, 
        db: AsyncSession, 
        person_id: int
    ) -> Optional[Person]:
        """
        Get a person with their organizations.
        
        Args:
            db: Database session
            person_id: ID of the person to get
            
        Returns:
            The person with organizations if found, None otherwise
        """
        query = select(Person).options(
            selectinload(Person.organizations)
        ).where(Person.person_id == person_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_sessions(
        self, 
        db: AsyncSession, 
        person_id: int
    ) -> Optional[Person]:
        """
        Get a person with their speaking sessions.
        
        Args:
            db: Database session
            person_id: ID of the person to get
            
        Returns:
            The person with speaking sessions if found, None otherwise
        """
        query = select(Person).options(
            selectinload(Person.speaking_sessions)
        ).where(Person.person_id == person_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_with_all_relations(
        self, 
        db: AsyncSession, 
        person_id: int
    ) -> Optional[Person]:
        """
        Get a person with all their relations (papers, organizations, sessions).
        
        Args:
            db: Database session
            person_id: ID of the person to get
            
        Returns:
            The person with all relations if found, None otherwise
        """
        query = select(Person).options(
            selectinload(Person.authored_papers),
            selectinload(Person.organizations),
            selectinload(Person.speaking_sessions)
        ).where(Person.person_id == person_id)
        result = await db.execute(query)
        return result.scalars().first()


class OrganizationRepository(BaseRepository[Organization, None, None]):
    """
    Repository for Organization model with custom methods.
    """
    
    def __init__(self):
        super().__init__(Organization)
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Organization]:
        """
        Get an organization by name.
        
        Args:
            db: Database session
            name: Name of the organization to get
            
        Returns:
            The organization if found, None otherwise
        """
        query = select(Organization).where(func.lower(Organization.name) == func.lower(name))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_organizations_by_person(
        self, 
        db: AsyncSession, 
        person_id: int
    ) -> List[Organization]:
        """
        Get all organizations for a person.
        
        Args:
            db: Database session
            person_id: ID of the person
            
        Returns:
            List of organizations
        """
        query = select(Organization).where(
            Organization.person_id == person_id
        ).order_by(Organization.name)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_organizations_by_country(
        self, 
        db: AsyncSession, 
        country: str
    ) -> List[Organization]:
        """
        Get all organizations from a specific country.
        
        Args:
            db: Database session
            country: Country to filter by
            
        Returns:
            List of organizations
        """
        query = select(Organization).where(
            func.lower(Organization.country) == func.lower(country)
        ).order_by(Organization.name)
        result = await db.execute(query)
        return result.scalars().all()