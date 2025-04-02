from app.repositories.base import BaseRepository
from app.repositories.user import UserRepository
from app.repositories.conference import ConferenceRepository, ConferenceInstanceRepository
from app.repositories.paper import PaperRepository, KeywordRepository, ReferenceRepository
from app.repositories.person import PersonRepository, OrganizationRepository
from app.repositories.session import SessionRepository
from app.repositories.report import ReportRepository, ReportVersionRepository
from app.repositories.notebook import NotebookRepository, NotebookSnapshotRepository

# Import all repositories here to make them available when importing from app.repositories