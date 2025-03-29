from fastapi import APIRouter
from .routes.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(tasks_router)