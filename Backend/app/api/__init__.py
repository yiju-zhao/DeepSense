from fastapi import APIRouter
from .routes.publications import router as publications_router
from .routes.reports import router as reports_router
from .routes.reviews import router as reviews_router
from .routes.crawler_tasks import router as crawler_router

api_router = APIRouter()
api_router.include_router(publications_router)
api_router.include_router(reports_router)
api_router.include_router(reviews_router)
api_router.include_router(crawler_router)
