"""Integration tests for Phase 2.2 Analytics API endpoints."""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import DailyActivity, RatingHistory, Submission, TagStats
from app.models.user_handle import HandlePlatform, HandleStatus, HandleSyncStatus, UserHandle
from app.services.analytics import _compute_streaks, get_dashboard, get_rating_history, get_tag_stats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def verified_handle(db_session: AsyncSession, test_user):
    handle = UserHandle(
        user_id=test_user.id,
        platform=HandlePlatform.CODEFORCES,
        handle="tourist",
        is_verified=True,
        is_active=True,
        status=HandleStatus.ACTIVE,
        sync_status=HandleSyncStatus.IDLE,
    )
    db_session.add(handle)
    await db_session.commit()
    await db_session.refresh(handle)
    yield handle
    await db_session.delete(handle)
    await db_session.commit()


@pytest_asyncio.fixture
async def daily_activity_rows(db_session: AsyncSession, verified_handle):
    today = date.today()
    rows = [
        DailyActivity(user_handle_id=verified_handle.id, activity_date=today, solved_count=3, submission_count=5),
        DailyActivity(user_handle_id=verified_handle.id, activity_date=today - timedelta(days=1), solved_count=2, submission_count=3),
        DailyActivity(user_handle_id=verified_handle.id, activity_date=today - timedelta(days=2), solved_count=0, submission_count=1),
        DailyActivity(user_handle_id=verified_handle.id, activity_date=today - timedelta(days=3), solved_count=5, submission_count=6),
        # A row older than 365 days — should NOT appear in heatmap but must count toward total_solved
        DailyActivity(user_handle_id=verified_handle.id, activity_date=today - timedelta(days=400), solved_count=10, submission_count=12),
    ]
    for r in rows:
        db_session.add(r)
    await db_session.commit()
    yield rows
    for r in rows:
        await db_session.delete(r)
    await db_session.commit()


@pytest_asyncio.fixture
async def submission_rows(db_session: AsyncSession, verified_handle):
    """7 distinct OK problems + 1 WA + 1 duplicate OK (same problem_id) = 7 distinct solved."""
    today = datetime.now(UTC)
    rows = [
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9001, problem_id="1A", problem_name="P1", verdict="OK", lang="C++", submitted_at=today),
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9002, problem_id="1B", problem_name="P2", verdict="OK", lang="C++", submitted_at=today),
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9003, problem_id="1C", problem_name="P3", verdict="OK", lang="C++", submitted_at=today),
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9004, problem_id="2A", problem_name="P4", verdict="OK", lang="C++", submitted_at=today),
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9005, problem_id="2B", problem_name="P5", verdict="OK", lang="C++", submitted_at=today),
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9006, problem_id="2C", problem_name="P6", verdict="OK", lang="C++", submitted_at=today),
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9007, problem_id="3A", problem_name="P7", verdict="OK", lang="C++", submitted_at=today),
        # WA submission — should NOT count toward total_solved
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9008, problem_id="3B", problem_name="P8", verdict="WRONG_ANSWER", lang="C++", submitted_at=today),
        # Duplicate OK on same problem_id as 9001 — should not increase distinct count
        Submission(user_handle_id=verified_handle.id, cf_submission_id=9009, problem_id="1A", problem_name="P1", verdict="OK", lang="C++", submitted_at=today),
    ]
    for r in rows:
        db_session.add(r)
    await db_session.commit()
    yield rows
    for r in rows:
        await db_session.delete(r)
    await db_session.commit()


@pytest_asyncio.fixture
async def tag_stats_rows(db_session: AsyncSession, verified_handle):
    rows = [
        TagStats(user_handle_id=verified_handle.id, tag="dp", solved_count=20, attempt_count=25, acceptance_rate=0.8),
        TagStats(user_handle_id=verified_handle.id, tag="graphs", solved_count=10, attempt_count=15, acceptance_rate=0.67),
        TagStats(user_handle_id=verified_handle.id, tag="math", solved_count=30, attempt_count=35, acceptance_rate=0.86),
    ]
    for r in rows:
        db_session.add(r)
    await db_session.commit()
    yield rows
    for r in rows:
        await db_session.delete(r)
    await db_session.commit()


@pytest_asyncio.fixture
async def rating_history_rows(db_session: AsyncSession, verified_handle):
    base = datetime(2024, 1, 1, tzinfo=UTC)
    rows = [
        RatingHistory(
            user_handle_id=verified_handle.id,
            cf_contest_id=1001,
            contest_name="Codeforces Round 900",
            old_rating=1400,
            new_rating=1500,
            delta=100,
            rank=150,
            contest_time=base,
        ),
        RatingHistory(
            user_handle_id=verified_handle.id,
            cf_contest_id=1002,
            contest_name="Codeforces Round 901",
            old_rating=1500,
            new_rating=1600,
            delta=100,
            rank=80,
            contest_time=base + timedelta(days=30),
        ),
        RatingHistory(
            user_handle_id=verified_handle.id,
            cf_contest_id=1003,
            contest_name="Codeforces Round 902",
            old_rating=1600,
            new_rating=1550,
            delta=-50,
            rank=300,
            contest_time=base + timedelta(days=60),
        ),
    ]
    for r in rows:
        db_session.add(r)
    await db_session.commit()
    yield rows
    for r in rows:
        await db_session.delete(r)
    await db_session.commit()


# ---------------------------------------------------------------------------
# Unit tests for streak logic
# ---------------------------------------------------------------------------


def test_streak_consecutive_from_today():
    today = date.today()
    data = {
        today: 3,
        today - timedelta(days=1): 2,
        today - timedelta(days=2): 1,
    }
    current, longest = _compute_streaks(data)
    assert current == 3
    assert longest == 3


def test_streak_grace_day_yesterday_counts():
    today = date.today()
    data = {
        today: 0,                        # no activity today yet
        today - timedelta(days=1): 5,    # but yesterday had solves
        today - timedelta(days=2): 5,
    }
    current, longest = _compute_streaks(data)
    assert current == 2   # grace day: yesterday is the effective "today"
    assert longest == 2


def test_streak_grace_day_no_streak():
    today = date.today()
    data = {
        today: 0,
        today - timedelta(days=1): 0,   # yesterday also empty → no grace day
        today - timedelta(days=2): 5,
    }
    current, longest = _compute_streaks(data)
    assert current == 0
    assert longest == 1


def test_streak_gap_in_history():
    today = date.today()
    data = {
        today: 2,
        today - timedelta(days=1): 1,
        today - timedelta(days=3): 4,  # gap at day-2
        today - timedelta(days=4): 3,
    }
    current, longest = _compute_streaks(data)
    assert current == 2
    assert longest == 2


# ---------------------------------------------------------------------------
# Dashboard — no handle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_no_handle_returns_zeros(db_session: AsyncSession, test_user):
    result = await get_dashboard(db_session, test_user.id)
    assert result.heatmap == []
    assert result.current_streak == 0
    assert result.longest_streak == 0
    assert result.total_solved == 0
    assert result.cf_rating is None
    assert result.has_verified_handle is False


# ---------------------------------------------------------------------------
# Dashboard — with data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_heatmap_excludes_old_rows(db_session: AsyncSession, test_user, verified_handle, daily_activity_rows):
    result = await get_dashboard(db_session, test_user.id)
    heatmap_dates = {d.date for d in result.heatmap}
    old_date = (date.today() - timedelta(days=400)).isoformat()
    assert old_date not in heatmap_dates


@pytest.mark.asyncio
async def test_dashboard_heatmap_excludes_zero_solved_days(db_session: AsyncSession, test_user, verified_handle, daily_activity_rows):
    result = await get_dashboard(db_session, test_user.id)
    assert all(d.count > 0 for d in result.heatmap)


@pytest.mark.asyncio
async def test_dashboard_total_solved_includes_old_rows(db_session: AsyncSession, test_user, verified_handle, submission_rows):
    # 7 distinct OK problem_ids (1A submitted twice → still counts once; 3B is WA → excluded)
    result = await get_dashboard(db_session, test_user.id)
    assert result.total_solved == 7


@pytest.mark.asyncio
async def test_dashboard_current_streak(db_session: AsyncSession, test_user, verified_handle, daily_activity_rows):
    # Streak uses submission_count (any submission = CF definition).
    # submission_count: today=5, day-1=3, day-2=1, day-3=6 — all consecutive, none zero.
    # day-400 is isolated (397-day gap). Current streak = 4 (day-3 through today).
    result = await get_dashboard(db_session, test_user.id)
    assert result.current_streak == 4


@pytest.mark.asyncio
async def test_dashboard_longest_streak(db_session: AsyncSession, test_user, verified_handle, daily_activity_rows):
    # submission_count: day-3=6, day-2=1, day-1=3, today=5 — all > 0, consecutive.
    # day-400 is isolated. Longest run = 4.
    result = await get_dashboard(db_session, test_user.id)
    assert result.longest_streak == 4


@pytest.mark.asyncio
async def test_dashboard_cf_rating_from_latest_contest(db_session: AsyncSession, test_user, verified_handle, rating_history_rows):
    result = await get_dashboard(db_session, test_user.id)
    # Most recent: new_rating=1550
    assert result.cf_rating == 1550


# ---------------------------------------------------------------------------
# Tag stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tag_stats_no_handle_returns_empty(db_session: AsyncSession, test_user):
    result = await get_tag_stats(db_session, test_user.id)
    assert result == []


@pytest.mark.asyncio
async def test_tag_stats_sorted_by_solved_count_desc(db_session: AsyncSession, test_user, verified_handle, tag_stats_rows):
    result = await get_tag_stats(db_session, test_user.id)
    counts = [r.solved_count for r in result]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.asyncio
async def test_tag_stats_all_fields_present(db_session: AsyncSession, test_user, verified_handle, tag_stats_rows):
    result = await get_tag_stats(db_session, test_user.id)
    assert len(result) == 3
    tags = {r.tag for r in result}
    assert tags == {"dp", "graphs", "math"}


# ---------------------------------------------------------------------------
# Rating history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rating_history_no_handle_returns_empty(db_session: AsyncSession, test_user):
    result = await get_rating_history(db_session, test_user.id)
    assert result == []


@pytest.mark.asyncio
async def test_rating_history_ordered_by_contest_time_asc(db_session: AsyncSession, test_user, verified_handle, rating_history_rows):
    result = await get_rating_history(db_session, test_user.id)
    times = [r.contest_time for r in result]
    assert times == sorted(times)


@pytest.mark.asyncio
async def test_rating_history_all_fields_present(db_session: AsyncSession, test_user, verified_handle, rating_history_rows):
    result = await get_rating_history(db_session, test_user.id)
    assert len(result) == 3
    assert result[0].cf_contest_id == 1001
    assert result[0].new_rating == 1500
    assert result[2].delta == -50


# ── Sync-on-view ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_sync_on_view_enqueues_when_stale(
    db_session: AsyncSession, test_user, verified_handle, monkeypatch
):
    from fastapi import BackgroundTasks

    verified_handle.last_synced_at = datetime.now(UTC) - timedelta(hours=1)
    await db_session.commit()

    enqueued: list = []
    monkeypatch.setattr(
        "app.services.analytics.enqueue_sync",
        lambda hid, bt: enqueued.append(hid) or "task",
    )

    result = await get_dashboard(db_session, test_user.id, BackgroundTasks())
    assert enqueued == [verified_handle.id]
    assert result.is_syncing is True
    # Sync-on-view must not consume the manual-button cooldown.
    await db_session.refresh(verified_handle)
    assert verified_handle.last_manual_sync_at is None


@pytest.mark.asyncio
async def test_dashboard_sync_on_view_skips_when_fresh(
    db_session: AsyncSession, test_user, verified_handle, monkeypatch
):
    from fastapi import BackgroundTasks

    verified_handle.last_synced_at = datetime.now(UTC) - timedelta(seconds=30)
    await db_session.commit()

    enqueued: list = []
    monkeypatch.setattr(
        "app.services.analytics.enqueue_sync",
        lambda hid, bt: enqueued.append(hid) or "task",
    )

    result = await get_dashboard(db_session, test_user.id, BackgroundTasks())
    assert enqueued == []
    assert result.is_syncing is False
