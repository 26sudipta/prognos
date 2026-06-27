"""Integration tests for Phase 3.2 Contest API — real DB, service layer."""

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Contest
from app.services.contests import get_contests, get_contests_calendar, get_platforms

# Test clist_ids kept in a dedicated range to avoid collisions
_TEST_IDS = list(range(8000, 8020))

# Base date far enough in the future that CLIST (30-day lookahead) will never
# have real data here, so seeded rows are the only rows in this window.
_BASE = datetime(2028, 7, 1, 10, 0, 0, tzinfo=UTC)
_FROM = datetime(2028, 7, 1, tzinfo=UTC)
_TO   = datetime(2028, 8, 1, tzinfo=UTC)


def _make_contest_row(
    clist_id: int,
    platform: str = "codeforces.com",
    name: str | None = None,
    start_offset_days: int = 1,
) -> Contest:
    start = _BASE + timedelta(days=start_offset_days)
    return Contest(
        clist_id=clist_id,
        platform=platform,
        name=name or f"Contest {clist_id}",
        start_time=start,
        end_time=start + timedelta(hours=2),
        duration_seconds=7200,
        url=f"https://example.com/{clist_id}",
        last_synced_at=datetime.now(UTC),
    )


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Contest).where(Contest.clist_id.in_(_TEST_IDS)))
    await db_session.commit()


@pytest_asyncio.fixture
async def seeded_contests(db_session: AsyncSession):
    rows = [
        _make_contest_row(8000, platform="codeforces.com", name="CF Round 1", start_offset_days=1),
        _make_contest_row(8001, platform="codeforces.com", name="CF Round 2", start_offset_days=2),
        _make_contest_row(8002, platform="atcoder.jp", name="AtCoder ABC", start_offset_days=1),
        _make_contest_row(8003, platform="atcoder.jp", name="AtCoder ARC", start_offset_days=3),
    ]
    for r in rows:
        db_session.add(r)
    await db_session.commit()
    return rows


# ---------------------------------------------------------------------------
# get_contests — list + filtering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_contests_returns_all(db_session: AsyncSession, seeded_contests):
    result = await get_contests(db_session, platform=None, from_dt=_FROM, to_dt=_TO, limit=50, offset=0)

    assert result.total == 4
    assert len(result.contests) == 4


@pytest.mark.asyncio
async def test_get_contests_filters_by_platform(db_session: AsyncSession, seeded_contests):
    result = await get_contests(
        db_session, platform=["codeforces.com"], from_dt=_FROM, to_dt=_TO, limit=50, offset=0
    )

    assert result.total == 2
    assert all(c.platform == "codeforces.com" for c in result.contests)


@pytest.mark.asyncio
async def test_get_contests_filters_by_multiple_platforms(db_session: AsyncSession, seeded_contests):
    result = await get_contests(
        db_session, platform=["codeforces.com", "atcoder.jp"], from_dt=_FROM, to_dt=_TO, limit=50, offset=0
    )

    assert result.total == 4
    platforms_found = {c.platform for c in result.contests}
    assert platforms_found == {"codeforces.com", "atcoder.jp"}


@pytest.mark.asyncio
async def test_get_contests_pagination(db_session: AsyncSession, seeded_contests):
    page1 = await get_contests(db_session, platform=None, from_dt=_FROM, to_dt=_TO, limit=2, offset=0)
    page2 = await get_contests(db_session, platform=None, from_dt=_FROM, to_dt=_TO, limit=2, offset=2)

    assert len(page1.contests) == 2
    assert len(page2.contests) == 2
    assert page1.total == 4
    ids_page1 = {c.clist_id for c in page1.contests}
    ids_page2 = {c.clist_id for c in page2.contests}
    assert ids_page1.isdisjoint(ids_page2)


@pytest.mark.asyncio
async def test_get_contests_sorted_by_start_time(db_session: AsyncSession, seeded_contests):
    result = await get_contests(db_session, platform=None, from_dt=_FROM, to_dt=_TO, limit=50, offset=0)

    times = [c.start_time for c in result.contests]
    assert times == sorted(times)


@pytest.mark.asyncio
async def test_get_contests_empty_outside_window(db_session: AsyncSession, seeded_contests):
    # Window before any test contests
    from_dt = datetime(2025, 1, 1, tzinfo=UTC)
    to_dt   = datetime(2025, 12, 31, tzinfo=UTC)

    result = await get_contests(db_session, platform=None, from_dt=from_dt, to_dt=to_dt, limit=50, offset=0)

    assert result.total == 0
    assert result.contests == []


# ---------------------------------------------------------------------------
# get_contests_calendar — grouping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_contests_calendar_groups_by_date(db_session: AsyncSession, seeded_contests):
    """2028-07-02 has 2 contests (CF+AtCoder), 2028-07-03 has 1 (CF), 2028-07-04 has 1 (AtCoder)."""
    result = await get_contests_calendar(db_session, platform=None, from_dt=_FROM, to_dt=_TO)

    assert len(result.days) == 3
    day_map = {d.date: len(d.contests) for d in result.days}
    assert day_map["2028-07-02"] == 2
    assert day_map["2028-07-03"] == 1
    assert day_map["2028-07-04"] == 1


@pytest.mark.asyncio
async def test_get_contests_calendar_platform_filter(db_session: AsyncSession, seeded_contests):
    result = await get_contests_calendar(db_session, platform=["atcoder.jp"], from_dt=_FROM, to_dt=_TO)

    all_platforms = {c.platform for day in result.days for c in day.contests}
    assert all_platforms == {"atcoder.jp"}


# ---------------------------------------------------------------------------
# get_platforms
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_contests_pagination_stable_with_tied_start_times(db_session: AsyncSession):
    """Pagination must be deterministic when multiple contests share the same start_time."""
    same_start = datetime(2028, 7, 10, 10, 0, 0, tzinfo=UTC)
    rows = [
        Contest(
            clist_id=8010 + i,
            platform="codeforces.com",
            name=f"Tie Contest {i}",
            start_time=same_start,
            end_time=same_start + timedelta(hours=2),
            duration_seconds=7200,
            url=f"https://example.com/tie/{i}",
            last_synced_at=datetime.now(UTC),
        )
        for i in range(4)
    ]
    for r in rows:
        db_session.add(r)
    await db_session.commit()

    page1 = await get_contests(db_session, platform=None, from_dt=_FROM, to_dt=_TO, limit=2, offset=0)
    page2 = await get_contests(db_session, platform=None, from_dt=_FROM, to_dt=_TO, limit=2, offset=2)

    ids_page1 = {c.clist_id for c in page1.contests}
    ids_page2 = {c.clist_id for c in page2.contests}
    # No row appears on both pages, no row is missing
    assert ids_page1.isdisjoint(ids_page2)
    assert ids_page1 | ids_page2 == {8010, 8011, 8012, 8013}


@pytest.mark.asyncio
async def test_get_platforms_returns_distinct_sorted(db_session: AsyncSession):
    """Platforms live in the now-to-now+30d window; seed with relative offsets so this never expires."""
    now = datetime.now(UTC)
    rows = [
        Contest(
            clist_id=8016,
            platform="codeforces.com",
            name="Future CF",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
            duration_seconds=7200,
            url="https://example.com/8016",
            last_synced_at=now,
        ),
        Contest(
            clist_id=8017,
            platform="atcoder.jp",
            name="Future AC",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=2),
            duration_seconds=7200,
            url="https://example.com/8017",
            last_synced_at=now,
        ),
    ]
    for r in rows:
        db_session.add(r)
    await db_session.commit()

    platforms = await get_platforms(db_session)

    # Must include both seeded platforms
    assert "atcoder.jp" in platforms
    assert "codeforces.com" in platforms
    # Must be sorted
    assert platforms == sorted(platforms)
    # No duplicates
    assert len(platforms) == len(set(platforms))
