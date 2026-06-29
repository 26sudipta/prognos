"""
Cron trigger endpoints — replace the Celery beat schedule in the worker-free
(free-tier) deployment. An external scheduler (cron-job.org) calls these with
the shared `X-Cron-Secret` header; the work runs via FastAPI BackgroundTasks.

Local/Celery deployments can ignore these — beat still drives sync there.
"""

import secrets
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user_handle import UserHandle
from app.workers.cf_sync import _sync_handle_async
from app.workers.clist_sync import _run_sync as run_clist_sync

router = APIRouter(prefix="/cron", tags=["cron"])


def _verify_cron_secret(provided: str | None) -> None:
    """Reject unless the header matches a configured non-empty CRON_SECRET."""
    if (
        not settings.CRON_SECRET
        or not provided
        or not secrets.compare_digest(provided, settings.CRON_SECRET)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing cron secret",
        )


@router.post("/sync-contests", status_code=status.HTTP_202_ACCEPTED)
async def cron_sync_contests(
    background_tasks: BackgroundTasks,
    x_cron_secret: str | None = Header(default=None),
) -> dict:
    """Refresh the global contest cache from CLIST (replaces the 4h beat)."""
    _verify_cron_secret(x_cron_secret)
    background_tasks.add_task(run_clist_sync)
    return {"status": "scheduled", "task": "sync-contests"}


@router.post("/sync-handles", status_code=status.HTTP_202_ACCEPTED)
async def cron_sync_handles(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    x_cron_secret: str | None = Header(default=None),
) -> dict:
    """Sync every active verified handle (replaces the 6h beat).

    BackgroundTasks run sequentially after the response, so handles are synced
    one after another — naturally friendly to the Codeforces rate limit.
    """
    _verify_cron_secret(x_cron_secret)
    result = await db.execute(
        select(UserHandle.id).where(
            UserHandle.is_verified.is_(True),
            UserHandle.is_active.is_(True),
        )
    )
    handle_ids: list[uuid.UUID] = list(result.scalars().all())
    for hid in handle_ids:
        background_tasks.add_task(_sync_handle_async, hid)
    return {"status": "scheduled", "task": "sync-handles", "count": len(handle_ids)}
