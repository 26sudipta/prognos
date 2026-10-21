"""Classroom v2 Slice 1a: participant type, team id and the cf_problems catalogue.

Codeforces is mocked at `_cf_get` / `_get_cf_problemset`, so these run offline.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.analytics import CfProblem, Submission
from app.models.user import User
from app.models.user_handle import HandlePlatform, HandleStatus, UserHandle
from app.workers.cf_sync import (
    _backfill_participant_types,
    _fetch_submissions,
    _refresh_cf_problems,
)


def _cf_sub(cf_id: int, ptype: str | None = "PRACTICE", team_id: int | None = None) -> dict:
    author: dict = {"members": [{"handle": "x"}]}
    if ptype is not None:
        author["participantType"] = ptype
    if team_id is not None:
        author["teamId"] = team_id
    return {
        "id": cf_id,
        "creationTimeSeconds": 1_760_000_000,
        "problem": {"contestId": 1903, "index": "A", "name": "Odd One Out", "tags": ["math"]},
        "author": author,
        "verdict": "OK",
        "programmingLanguage": "C++20",
    }


@pytest_asyncio.fixture
async def handle(db_session, test_user: User):
    row = UserHandle(
        user_id=test_user.id,
        platform=HandlePlatform.CODEFORCES,
        handle=f"fid_{uuid.uuid4().hex[:6]}",
        status=HandleStatus.ACTIVE,
        is_verified=True,
        is_active=True,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    yield row


async def _subs(db, handle_id):
    rows = await db.execute(
        select(Submission.cf_submission_id, Submission.participant_type, Submission.team_id)
        .where(Submission.user_handle_id == handle_id)
        .order_by(Submission.cf_submission_id)
    )
    return [tuple(r) for r in rows.all()]


async def _seed_old_rows(db, handle_id, cf_ids):
    """Rows as they looked before migration 011: no participant type."""
    for cf_id in cf_ids:
        await db.execute(pg_insert(Submission).values(
            user_handle_id=handle_id, cf_submission_id=cf_id, problem_id="1903A",
            problem_name="Odd One Out", contest_id=1903, verdict="OK", lang="C++20",
            submitted_at=datetime.now(UTC),
        ))
    await db.commit()


# ── Ingest ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_stores_participant_type_and_team(db_session, handle):
    batch = [_cf_sub(103, "CONTESTANT"), _cf_sub(102, "PRACTICE", team_id=77), _cf_sub(101, None)]
    with patch("app.workers.cf_sync._cf_get", AsyncMock(return_value={"result": batch})):
        stored = await _fetch_submissions(handle.handle, handle.id, db_session)

    assert stored == 3
    assert await _subs(db_session, handle.id) == [
        (101, "UNKNOWN", None),   # missing author field never leaves a NULL behind
        (102, "PRACTICE", 77),
        (103, "CONTESTANT", None),
    ]


# ── Backfill ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_backfill_fills_old_rows_and_marks_vanished_ones(db_session, handle):
    await _seed_old_rows(db_session, handle.id, [1, 2, 3])
    cf = AsyncMock(
        return_value={"result": [_cf_sub(1, "CONTESTANT"), _cf_sub(2, "VIRTUAL", team_id=5)]}
    )
    with patch("app.workers.cf_sync._cf_get", cf):
        pending = await _backfill_participant_types(handle.handle, handle.id, db_session)

    assert pending == 3
    assert await _subs(db_session, handle.id) == [
        (1, "CONTESTANT", None),
        (2, "VIRTUAL", 5),
        (3, "UNKNOWN", None),     # deleted on CF: resolved once, never re-fetched
    ]

    # Second run: nothing pending, so no CF traffic at all.
    cf.reset_mock()
    with patch("app.workers.cf_sync._cf_get", cf):
        assert await _backfill_participant_types(handle.handle, handle.id, db_session) == 0
    cf.assert_not_called()


@pytest.mark.asyncio
async def test_backfill_leaves_rows_null_when_cf_fails(db_session, handle):
    await _seed_old_rows(db_session, handle.id, [11, 12])
    with patch("app.workers.cf_sync._cf_get", AsyncMock(side_effect=RuntimeError("CF down"))):
        with pytest.raises(RuntimeError):
            await _backfill_participant_types(handle.handle, handle.id, db_session)
    # Nothing written, so the next sync retries instead of marking everything UNKNOWN.
    assert await _subs(db_session, handle.id) == [(11, None, None), (12, None, None)]


@pytest.mark.asyncio
async def test_backfill_pages_through_long_histories(db_session, handle):
    await _seed_old_rows(db_session, handle.id, [1, 1500])
    page1 = [_cf_sub(i, "PRACTICE") for i in range(2000, 1000, -1)]   # exactly 1000 rows
    page2 = [_cf_sub(1000 - i, "CONTESTANT") for i in range(0, 999)] + [_cf_sub(1, "CONTESTANT")]
    cf = AsyncMock(side_effect=[{"result": page1}, {"result": page2[:500]}])
    no_sleep = patch("app.workers.cf_sync.asyncio.sleep", AsyncMock())
    with patch("app.workers.cf_sync._cf_get", cf), no_sleep:
        await _backfill_participant_types(handle.handle, handle.id, db_session)

    assert cf.await_count == 2
    rows = dict((cf_id, ptype) for cf_id, ptype, _ in await _subs(db_session, handle.id))
    assert rows[1500] == "PRACTICE"
    assert rows[1] == "UNKNOWN"   # id 1 sat beyond the second (short) page


# ── cf_problems catalogue ─────────────────────────────────────────────────────

PROBLEMS = [
    {"contestId": 1903, "index": "A", "name": "Odd One Out", "rating": 800, "tags": ["math"]},
    {"contestId": 1903, "index": "F2", "name": "Hard Version", "tags": ["dp"]},   # not rated yet
]


@pytest_asyncio.fixture
async def empty_catalogue(db_session):
    # Test DB only (conftest refuses non-local hosts): the freshness check reads the
    # whole table, so start from empty.
    await db_session.execute(delete(CfProblem))
    await db_session.commit()
    yield
    await db_session.execute(delete(CfProblem))
    await db_session.commit()


@pytest.mark.asyncio
async def test_refresh_cf_problems_upserts_then_skips_while_fresh(db_session, empty_catalogue):
    fetch = AsyncMock(return_value=PROBLEMS)
    with patch("app.workers.cf_sync._get_cf_problemset", fetch):
        assert await _refresh_cf_problems(db_session) == 2
        assert await _refresh_cf_problems(db_session) == 0   # within 24 h: no work
    fetch.assert_awaited_once()

    rows = {r.problem_key: r for r in (await db_session.execute(select(CfProblem))).scalars()}
    assert rows["1903A"].rating == 800 and rows["1903A"].tags == ["math"]
    assert rows["1903F2"].rating is None and rows["1903F2"].problem_index == "F2"


@pytest.mark.asyncio
async def test_refresh_cf_problems_picks_up_late_ratings(db_session, empty_catalogue):
    with patch("app.workers.cf_sync._get_cf_problemset", AsyncMock(return_value=PROBLEMS)):
        await _refresh_cf_problems(db_session)

    # A day later Codeforces has rated F2.
    await db_session.execute(
        update(CfProblem).values(updated_at=datetime.now(UTC) - timedelta(hours=25))
    )
    await db_session.commit()
    rated = [dict(p) for p in PROBLEMS]
    rated[1]["rating"] = 2400
    with patch("app.workers.cf_sync._get_cf_problemset", AsyncMock(return_value=rated)):
        assert await _refresh_cf_problems(db_session) == 2

    row = (
        await db_session.execute(
            select(CfProblem).where(CfProblem.problem_key == "1903F2")
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert row.rating == 2400
