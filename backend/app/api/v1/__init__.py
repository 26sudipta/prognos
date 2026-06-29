from fastapi import APIRouter

from app.api.v1.routes.analytics import router as analytics_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.classrooms import router as classrooms_router
from app.api.v1.routes.contests import router as contests_router
from app.api.v1.routes.cron import router as cron_router
from app.api.v1.routes.handles import router as handles_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["system"])
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(handles_router)
api_router.include_router(analytics_router)
api_router.include_router(contests_router)
api_router.include_router(classrooms_router)
api_router.include_router(cron_router)
