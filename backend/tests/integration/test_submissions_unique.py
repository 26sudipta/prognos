"""Submissions uniqueness is per-handle, not global.

Regression test for the blank-dashboard bug: after a re-verify creates a new handle row,
the new handle re-fetches the same CF submission ids. Under the old GLOBAL unique on
cf_submission_id, those inserts were no-op'd (the ids already existed under the old
handle) → 0 rows stored under the active handle → empty dashboard. With the composite
unique (user_handle_id, cf_submission_id) each handle stores its own copy.
"""
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.analytics import Submission
from app.models.user import User
from app.models.user_handle import HandlePlatform, HandleStatus, UserHandle

CF_ID = 189551898  # tourist would be jealous — it's the real Watermelon submission id


async def _mk_handle(db, user_id, *, is_active: bool) -> UserHandle:
    row = UserHandle(
        user_id=user_id,
        platform=HandlePlatform.CODEFORCES,
        handle="Sudipta_Das",
        status=HandleStatus.ACTIVE,
        is_verified=True,
        is_active=is_active,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


def _insert_submission(handle_id: uuid.UUID, cf_id: int):
    return pg_insert(Submission).values(
        user_handle_id=handle_id,
        cf_submission_id=cf_id,
        problem_id="4A",
        problem_name="Watermelon",
        verdict="OK",
        lang="GNU C++",
        submitted_at=datetime.now(UTC),
    ).on_conflict_do_nothing(index_elements=["user_handle_id", "cf_submission_id"])


@pytest.mark.asyncio
async def test_same_cf_submission_id_stores_under_each_handle(
    db_session, test_user: User
):
    # Old (unlinked) row + new (active) row — the post-re-verify state.
    old = await _mk_handle(db_session, test_user.id, is_active=False)
    new = await _mk_handle(db_session, test_user.id, is_active=True)

    r_old = await db_session.execute(_insert_submission(old.id, CF_ID))
    r_new = await db_session.execute(_insert_submission(new.id, CF_ID))
    await db_session.commit()

    # The whole bug: r_new used to be 0 (global-unique no-op). Now both store.
    assert r_old.rowcount == 1
    assert r_new.rowcount == 1

    # A duplicate under the SAME handle is still a no-op (idempotent re-sync).
    r_dup = await db_session.execute(_insert_submission(new.id, CF_ID))
    await db_session.commit()
    assert r_dup.rowcount == 0

    # The active handle now actually has its submission → dashboard would be non-empty.
    active_count = (
        await db_session.execute(
            select(func.count())
            .select_from(Submission)
            .where(Submission.user_handle_id == new.id)
        )
    ).scalar_one()
    assert active_count == 1

    # Cleanup (submissions cascade when the handles are deleted).
    await db_session.delete(old)
    await db_session.delete(new)
    await db_session.commit()
