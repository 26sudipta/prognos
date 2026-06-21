import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_handle import HandlePlatform, HandleStatus, HandleSyncStatus, UserHandle


async def _create_handle(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    handle: str,
    is_active: bool = True,
) -> UserHandle:
    uh = UserHandle(
        user_id=user_id,
        platform=HandlePlatform.CODEFORCES,
        handle=handle,
        is_active=is_active,
        status=HandleStatus.ACTIVE,
        sync_status=HandleSyncStatus.IDLE,
    )
    db_session.add(uh)
    await db_session.flush()
    return uh


async def test_only_one_active_handle_per_user_platform(db_session, test_user):
    await _create_handle(db_session, test_user.id, "tourist")
    await db_session.commit()

    savepoint = await db_session.begin_nested()
    try:
        await _create_handle(db_session, test_user.id, "second_active_handle")
        pytest.fail("Expected IntegrityError was not raised")
    except IntegrityError:
        await savepoint.rollback()


async def test_multiple_inactive_handles_allowed(db_session, test_user):
    await _create_handle(db_session, test_user.id, "old_handle_1", is_active=False)
    await _create_handle(db_session, test_user.id, "old_handle_2", is_active=False)
    await db_session.commit()

    result = await db_session.execute(
        select(UserHandle).where(
            UserHandle.user_id == test_user.id,
            UserHandle.is_active == False,  # noqa: E712
        )
    )
    assert len(result.scalars().all()) == 2
