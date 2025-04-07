from fastapi import APIRouter
from .routes.tasks import router as tasks_router
from .routes.frontend_adapter import router as frontend_adapter_router

api_router = APIRouter()
api_router.include_router(tasks_router)
api_router.include_router(frontend_adapter_router)