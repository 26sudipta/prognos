from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "prognos",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.cf_sync"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    # Sync all active verified handles every 6 hours
    "cf-sync-all-handles": {
        "task": "app.workers.cf_sync.sync_all_handles",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}
