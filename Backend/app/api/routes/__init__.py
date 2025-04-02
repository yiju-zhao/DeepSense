from fastapi import APIRouter

from app.api.routes.auth import router as auth_router

# Create API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# Add more routers here as they are implemented
# Example:
# from app.api.routes.conferences import router as conferences_router
# api_router.include_router(conferences_router, prefix="/conferences", tags=["conferences"])