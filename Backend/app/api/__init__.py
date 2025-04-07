<<<<<<< HEAD
from fastapi import APIRouter
from .routes.tasks import router as tasks_router
from .routes.frontend_adapter import router as frontend_adapter_router

api_router = APIRouter()
api_router.include_router(tasks_router)
api_router.include_router(frontend_adapter_router)
=======
from app.api.routes import api_router
from app.api.errors import add_error_handlers
from app.api.middleware import add_logging_middleware

# Import all API components here to make them available when importing from app.api
>>>>>>> origin/main
