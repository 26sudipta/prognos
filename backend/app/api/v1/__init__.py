from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["system"])
api_router.include_router(auth_router)
api_router.include_router(users_router)
