import uuid

from fastapi import BackgroundTasks


def enqueue_sync(handle_id: uuid.UUID, background_tasks: BackgroundTasks) -> str:
    """Enqueue an authoritative Codeforces sync for a handle.

    Tries Celery first; falls back to a FastAPI background task when Celery/Redis
    is unavailable (free-tier deployment). Shared by the handles, analytics
    (sync-on-view) and classroom (bulk sync) routes so the enqueue policy lives
    in one place.
    """
    try:
        from app.workers.cf_sync import sync_handle

        task = sync_handle.delay(str(handle_id))
        return task.id
    except Exception:
        from app.workers.cf_sync import _sync_handle_async

        background_tasks.add_task(_sync_handle_async, handle_id)
        return str(uuid.uuid4())
