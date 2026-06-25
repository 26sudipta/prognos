"""Integration tests for Phase 2.3 Weakness + Recommendations endpoints."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signals import Recommendation, RecommendationSet, WeaknessSignal, WeaknessSignalType
from app.models.user_handle import HandlePlatform, HandleStatus, HandleSyncStatus, UserHandle
from app.services.analytics import get_recommendations, get_weaknesses


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
async def weakness_signal_rows(db_session: AsyncSession, verified_handle):
    rows = [
        WeaknessSignal(
            user_handle_id=verified_handle.id,
            tag="dp",
            signal_type=WeaknessSignalType.LOW_SUCCESS,
            score=0.85,
            reason="Low acceptance rate on dp problems",
        ),
        WeaknessSignal(
            user_handle_id=verified_handle.id,
            tag="graphs",
            signal_type=WeaknessSignalType.NEGLECTED,
            score=0.60,
            reason="No graphs problems attempted in 90 days",
        ),
        WeaknessSignal(
            user_handle_id=verified_handle.id,
            tag="math",
            signal_type=WeaknessSignalType.UNDER_PRACTICED,
            score=0.40,
            reason="Only 3 math problems solved",
        ),
    ]
    for r in rows:
        db_session.add(r)
    await db_session.commit()
    yield rows
    for r in rows:
        await db_session.delete(r)
    await db_session.commit()


def _make_rec_set(user_id, generated_at, problems):
    """Build a RecommendationSet with nested Recommendation rows (not yet added to session)."""
    rec_set = RecommendationSet(user_id=user_id, generated_at=generated_at)
    recs = [
        Recommendation(
            recommendation_set=rec_set,
            problem_id=p["problem_id"],
            problem_name=p["problem_name"],
            tag=p["tag"],
            difficulty=p["difficulty"],
            url=p["url"],
            reason=p["reason"],
            position=p["position"],
        )
        for p in problems
    ]
    return rec_set, recs


_SAMPLE_PROBLEMS = [
    {
        "problem_id": "1900A",
        "problem_name": "Cover it!",
        "tag": "dp",
        "difficulty": 1700,
        "url": "https://codeforces.com/problemset/problem/1900/A",
        "reason": "dp weakness",
        "position": 1,
    },
    {
        "problem_id": "1901B",
        "problem_name": "Coin Games",
        "tag": "graphs",
        "difficulty": 1500,
        "url": "https://codeforces.com/problemset/problem/1901/B",
        "reason": "graphs weakness",
        "position": 2,
    },
]


@pytest_asyncio.fixture
async def recommendation_set(db_session: AsyncSession, test_user):
    rec_set, recs = _make_rec_set(test_user.id, datetime(2026, 6, 25, tzinfo=UTC), _SAMPLE_PROBLEMS)
    db_session.add(rec_set)
    for r in recs:
        db_session.add(r)
    await db_session.commit()
    await db_session.refresh(rec_set)
    yield rec_set
    await db_session.delete(rec_set)
    await db_session.commit()


# ---------------------------------------------------------------------------
# Weaknesses — no handle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_weaknesses_no_handle_returns_empty(db_session: AsyncSession, test_user):
    result = await get_weaknesses(db_session, test_user.id)
    assert result == []


# ---------------------------------------------------------------------------
# Weaknesses — with data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_weaknesses_returns_all_signals(db_session: AsyncSession, test_user, verified_handle, weakness_signal_rows):
    result = await get_weaknesses(db_session, test_user.id)
    assert len(result) == 3
    tags = {r.tag for r in result}
    assert tags == {"dp", "graphs", "math"}


@pytest.mark.asyncio
async def test_weaknesses_sorted_by_score_desc(db_session: AsyncSession, test_user, verified_handle, weakness_signal_rows):
    result = await get_weaknesses(db_session, test_user.id)
    scores = [r.score for r in result]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_weaknesses_all_fields_present(db_session: AsyncSession, test_user, verified_handle, weakness_signal_rows):
    result = await get_weaknesses(db_session, test_user.id)
    top = next(r for r in result if r.tag == "dp")
    assert top.signal_type == WeaknessSignalType.LOW_SUCCESS
    assert top.score == pytest.approx(0.85)
    assert top.reason != ""
    assert top.computed_at is not None


# ---------------------------------------------------------------------------
# Recommendations — no data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recommendations_no_set_returns_none(db_session: AsyncSession, test_user):
    result = await get_recommendations(db_session, test_user.id)
    assert result is None


# ---------------------------------------------------------------------------
# Recommendations — with data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recommendations_returns_set_with_nested_items(db_session: AsyncSession, test_user, recommendation_set):
    result = await get_recommendations(db_session, test_user.id)
    assert result is not None
    assert len(result.recommendations) == 2


@pytest.mark.asyncio
async def test_recommendations_nested_sorted_by_position(db_session: AsyncSession, test_user, recommendation_set):
    result = await get_recommendations(db_session, test_user.id)
    positions = [r.position for r in result.recommendations]
    assert positions == sorted(positions)


@pytest.mark.asyncio
async def test_recommendations_returns_most_recent_set(db_session: AsyncSession, test_user):
    older_time = datetime(2026, 6, 20, tzinfo=UTC)
    newer_time = datetime(2026, 6, 25, tzinfo=UTC)

    older_set, older_recs = _make_rec_set(test_user.id, older_time, _SAMPLE_PROBLEMS)
    newer_set, newer_recs = _make_rec_set(test_user.id, newer_time, _SAMPLE_PROBLEMS[:1])

    for obj in [older_set, newer_set, *older_recs, *newer_recs]:
        db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(older_set)
    await db_session.refresh(newer_set)

    result = await get_recommendations(db_session, test_user.id)
    assert result is not None
    assert result.id == newer_set.id
    assert len(result.recommendations) == 1

    await db_session.delete(older_set)
    await db_session.delete(newer_set)
    await db_session.commit()
