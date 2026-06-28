"""
Codeforces sync worker.

Pipeline (in order after fetching submissions):
  1. Upsert submissions + submission_tags
  2. Recompute daily_activity
  3. Recompute tag_stats
  4. Upsert rating_history
  5. Compute weakness_signals
  6. Generate recommendations
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from celery import shared_task
from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.analytics import DailyActivity, RatingHistory, Submission, SubmissionTag, TagStats
from app.models.classroom import ClassroomMembership
from app.models.signals import Recommendation, RecommendationSet, WeaknessSignal, WeaknessSignalType
from app.models.user_handle import HandleSyncStatus, UserHandle

logger = logging.getLogger(__name__)

CF_API_BASE = "https://codeforces.com/api"
CF_PROBLEMSET_CACHE_KEY = "cf:problemset:all"
CF_PROBLEMSET_TTL = 3600 * 6  # 6 hours


def _make_engine():
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2", 1)
    from sqlalchemy import create_engine
    return create_engine(sync_url, pool_pre_ping=True)


def _make_async_engine():
    return create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_handle(self, handle_id: str) -> dict:
    """Sync a single handle. Called by manual-sync endpoint and beat."""
    try:
        return asyncio.run(_sync_handle_async(uuid.UUID(handle_id)))
    except Exception as exc:
        logger.exception("sync_handle failed for %s", handle_id)
        raise self.retry(exc=exc)


@shared_task
def sync_all_handles() -> None:
    """Beat task: enqueue sync for every active verified handle."""
    asyncio.run(_enqueue_all_handles())


# ---------------------------------------------------------------------------
# Async implementation
# ---------------------------------------------------------------------------

async def _enqueue_all_handles() -> None:
    engine = _make_async_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(
            select(UserHandle.id).where(
                UserHandle.is_verified == True,
                UserHandle.is_active == True,
            )
        )
        handle_ids = result.scalars().all()

    await engine.dispose()
    for hid in handle_ids:
        sync_handle.delay(str(hid))


async def _sync_handle_async(handle_id: uuid.UUID) -> dict:
    engine = _make_async_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        handle = await session.get(UserHandle, handle_id)
        if not handle:
            return {"error": "handle not found"}

        # Mark in_progress
        handle.sync_status = HandleSyncStatus.IN_PROGRESS
        await session.commit()

        try:
            submissions = await _fetch_submissions(handle.handle, handle_id, session)
            await _recompute_daily_activity(handle_id, session)
            await _recompute_tag_stats(handle_id, session)
            await _upsert_rating_history(handle.handle, handle_id, session)
            await _compute_weakness_signals(handle_id, session)
            await _generate_recommendations(handle_id, handle.user_id, session)

            handle.sync_status = HandleSyncStatus.COMPLETED
            handle.last_synced_at = datetime.now(UTC)
            handle.last_sync_error = None
            await session.commit()

            # Step 6: trigger leaderboard rebuild for every classroom this user belongs to
            await _trigger_leaderboard_rebuilds(handle.user_id, session)

            return {"synced": submissions}

        except Exception as exc:
            handle.sync_status = HandleSyncStatus.SYNC_ERROR
            handle.last_sync_error = str(exc)[:500]
            await session.commit()
            raise

    await engine.dispose()


# ---------------------------------------------------------------------------
# CF API helpers
# ---------------------------------------------------------------------------

async def _cf_get(client: httpx.AsyncClient, path: str, **params) -> dict:
    resp = await client.get(f"{CF_API_BASE}/{path}", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK":
        raise RuntimeError(f"CF API error: {data.get('comment', 'unknown')}")
    return data


async def _fetch_submissions(
    handle: str, handle_id: uuid.UUID, session: AsyncSession
) -> int:
    # Find max cf_submission_id already stored
    result = await session.execute(
        select(Submission.cf_submission_id)
        .where(Submission.user_handle_id == handle_id)
        .order_by(Submission.cf_submission_id.desc())
        .limit(1)
    )
    max_id = result.scalar_one_or_none() or 0

    new_submissions: list[dict] = []
    async with httpx.AsyncClient() as client:
        from_index = 1
        count = 500
        while True:
            data = await _cf_get(client, "user.status", handle=handle, from_=from_index, count=count)
            batch = data["result"]
            if not batch:
                break

            for s in batch:
                if s["id"] <= max_id:
                    # Reached already-synced submissions — stop
                    batch = []
                    break
                new_submissions.append(s)

            if not batch or len(batch) < count:
                break

            from_index += count
            await asyncio.sleep(2)  # CF rate limit

    if not new_submissions:
        return 0

    # Bulk insert via upsert (skip duplicates)
    for s in new_submissions:
        prob = s.get("problem", {})
        problem_id = f"{prob.get('contestId', '')}{prob.get('index', '')}"
        tags = prob.get("tags", [])

        stmt = pg_insert(Submission).values(
            user_handle_id=handle_id,
            cf_submission_id=s["id"],
            problem_id=problem_id,
            problem_name=prob.get("name", ""),
            contest_id=prob.get("contestId"),
            verdict=s.get("verdict", "UNKNOWN"),
            lang=s.get("programmingLanguage", ""),
            time_ms=s.get("timeConsumedMillis"),
            memory_kb=s.get("memoryConsumedBytes", 0) // 1024 if s.get("memoryConsumedBytes") else None,
            submitted_at=datetime.fromtimestamp(s["creationTimeSeconds"], tz=UTC),
        ).on_conflict_do_nothing(index_elements=["cf_submission_id"])

        result = await session.execute(stmt)
        if result.rowcount == 0:
            continue  # already exists

        # Get inserted row id
        sub_row = await session.execute(
            select(Submission.id).where(Submission.cf_submission_id == s["id"])
        )
        sub_id = sub_row.scalar_one()

        # Insert tags
        for tag in tags:
            await session.execute(
                pg_insert(SubmissionTag)
                .values(submission_id=sub_id, tag=tag)
                .on_conflict_do_nothing()
            )

    await session.commit()
    return len(new_submissions)


# ---------------------------------------------------------------------------
# Derived table recomputation
# ---------------------------------------------------------------------------

async def _recompute_daily_activity(handle_id: uuid.UUID, session: AsyncSession) -> None:
    # Delete and recompute from submissions
    await session.execute(
        delete(DailyActivity).where(DailyActivity.user_handle_id == handle_id)
    )
    await session.execute(
        text("""
            INSERT INTO daily_activity (user_handle_id, activity_date, submission_count, solved_count)
            SELECT
                s.user_handle_id,
                DATE(s.submitted_at AT TIME ZONE 'UTC') AS activity_date,
                COUNT(*) AS submission_count,
                COUNT(DISTINCT CASE WHEN s.verdict = 'OK' THEN s.problem_id END) AS solved_count
            FROM submissions s
            WHERE s.user_handle_id = :handle_id
            GROUP BY s.user_handle_id, DATE(s.submitted_at AT TIME ZONE 'UTC')
            ON CONFLICT (user_handle_id, activity_date) DO UPDATE
                SET submission_count = EXCLUDED.submission_count,
                    solved_count = EXCLUDED.solved_count
        """),
        {"handle_id": str(handle_id)},
    )
    await session.commit()


async def _recompute_tag_stats(handle_id: uuid.UUID, session: AsyncSession) -> None:
    await session.execute(
        text("""
            INSERT INTO tag_stats (user_handle_id, tag, solved_count, attempt_count, acceptance_rate, last_activity_at)
            SELECT
                s.user_handle_id,
                st.tag,
                COUNT(DISTINCT s.problem_id) FILTER (WHERE s.verdict = 'OK') AS solved_count,
                COUNT(DISTINCT s.problem_id) AS attempt_count,
                CASE
                    WHEN COUNT(DISTINCT s.problem_id) = 0 THEN 0
                    ELSE COUNT(DISTINCT s.problem_id) FILTER (WHERE s.verdict = 'OK')::float
                         / COUNT(DISTINCT s.problem_id)
                END AS acceptance_rate,
                MAX(s.submitted_at) AS last_activity_at
            FROM submissions s
            JOIN submission_tags st ON st.submission_id = s.id
            WHERE s.user_handle_id = :handle_id
            GROUP BY s.user_handle_id, st.tag
            ON CONFLICT (user_handle_id, tag) DO UPDATE
                SET solved_count     = EXCLUDED.solved_count,
                    attempt_count    = EXCLUDED.attempt_count,
                    acceptance_rate  = EXCLUDED.acceptance_rate,
                    last_activity_at = EXCLUDED.last_activity_at
        """),
        {"handle_id": str(handle_id)},
    )
    await session.commit()


async def _upsert_rating_history(
    handle: str, handle_id: uuid.UUID, session: AsyncSession
) -> None:
    async with httpx.AsyncClient() as client:
        try:
            data = await _cf_get(client, "user.rating", handle=handle)
        except Exception:
            return  # Unrated user — skip silently

    await session.execute(
        delete(RatingHistory).where(RatingHistory.user_handle_id == handle_id)
    )
    for entry in data["result"]:
        await session.execute(
            pg_insert(RatingHistory).values(
                user_handle_id=handle_id,
                cf_contest_id=entry["contestId"],
                contest_name=entry["contestName"],
                old_rating=entry["oldRating"],
                new_rating=entry["newRating"],
                delta=entry["newRating"] - entry["oldRating"],
                rank=entry["rank"],
                contest_time=datetime.fromtimestamp(entry["ratingUpdateTimeSeconds"], tz=UTC),
            ).on_conflict_do_nothing(index_elements=["user_handle_id", "cf_contest_id"])
        )
    await session.commit()


# ---------------------------------------------------------------------------
# Weakness signals
# ---------------------------------------------------------------------------

async def _compute_weakness_signals(handle_id: uuid.UUID, session: AsyncSession) -> None:
    now = datetime.now(UTC)
    neglect_threshold = now - timedelta(days=14)

    # Clear old signals for this handle
    await session.execute(
        delete(WeaknessSignal).where(WeaknessSignal.user_handle_id == handle_id)
    )

    result = await session.execute(
        select(TagStats).where(TagStats.user_handle_id == handle_id)
    )
    tag_rows = result.scalars().all()

    signals: list[WeaknessSignal] = []
    for row in tag_rows:
        # Neglected: solved at least once but no activity in 14+ days
        if row.solved_count >= 1 and row.last_activity_at and row.last_activity_at < neglect_threshold:
            days_since = (now - row.last_activity_at).days
            signals.append(WeaknessSignal(
                user_handle_id=handle_id,
                tag=row.tag,
                signal_type=WeaknessSignalType.NEGLECTED,
                score=min(days_since / 14.0, 5.0),
                reason=f"No activity in {days_since} days (last solved: {row.last_activity_at.date()})",
                computed_at=now,
            ))

        # Low success: tried 5+ problems but < 50% acceptance
        elif row.attempt_count >= 5 and row.acceptance_rate < 0.50:
            signals.append(WeaknessSignal(
                user_handle_id=handle_id,
                tag=row.tag,
                signal_type=WeaknessSignalType.LOW_SUCCESS,
                score=3.0 * (1.0 - row.acceptance_rate),
                reason=(
                    f"Acceptance rate {row.acceptance_rate:.0%} over "
                    f"{row.attempt_count} attempted problems"
                ),
                computed_at=now,
            ))

        # Under-practiced: solved fewer than 5 problems in this tag
        elif row.solved_count < 5:
            signals.append(WeaknessSignal(
                user_handle_id=handle_id,
                tag=row.tag,
                signal_type=WeaknessSignalType.UNDER_PRACTICED,
                score=1.0 + (5 - row.solved_count) * 0.4,
                reason=f"Only {row.solved_count} problem(s) solved in this tag",
                computed_at=now,
            ))

    session.add_all(signals)
    await session.commit()


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

async def _generate_recommendations(
    handle_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession
) -> None:
    # Get top 5 weakness tags by score
    result = await session.execute(
        select(WeaknessSignal)
        .where(WeaknessSignal.user_handle_id == handle_id)
        .order_by(WeaknessSignal.score.desc())
    )
    signals = result.scalars().all()

    # Deduplicate tags (take highest-score signal per tag)
    seen_tags: set[str] = set()
    top_tags: list[WeaknessSignal] = []
    for sig in signals:
        if sig.tag not in seen_tags:
            seen_tags.add(sig.tag)
            top_tags.append(sig)
        if len(top_tags) == 5:
            break

    if not top_tags:
        return

    # Get current user rating
    rating_result = await session.execute(
        select(RatingHistory.new_rating)
        .where(RatingHistory.user_handle_id == handle_id)
        .order_by(RatingHistory.contest_time.desc())
        .limit(1)
    )
    current_rating = rating_result.scalar_one_or_none() or 1200

    # Get solved problem_ids to exclude
    solved_result = await session.execute(
        select(Submission.problem_id)
        .where(Submission.user_handle_id == handle_id, Submission.verdict == "OK")
        .distinct()
    )
    solved_ids = set(solved_result.scalars().all())

    # Fetch CF problemset (with Redis cache)
    problems = await _get_cf_problemset()

    rec_set = RecommendationSet(user_id=user_id, generated_at=datetime.now(UTC))
    session.add(rec_set)
    await session.flush()  # get rec_set.id

    recs: list[Recommendation] = []
    for position, signal in enumerate(top_tags, start=1):
        problem = _pick_problem(signal.tag, current_rating, solved_ids, problems, expand=False)
        if not problem:
            problem = _pick_problem(signal.tag, current_rating, solved_ids, problems, expand=True)
        if not problem:
            continue

        contest_id = problem.get("contestId", "")
        index = problem.get("index", "")
        problem_id = f"{contest_id}{index}"
        recs.append(Recommendation(
            recommendation_set_id=rec_set.id,
            problem_id=problem_id,
            problem_name=problem.get("name", ""),
            tag=signal.tag,
            difficulty=problem.get("rating", 0),
            url=f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
            reason=signal.reason,
            position=position,
        ))

    session.add_all(recs)
    await session.commit()


def _pick_problem(
    tag: str,
    rating: int,
    solved_ids: set[str],
    problems: list[dict],
    expand: bool,
) -> dict | None:
    band = 200 if expand else 100
    low = max(800, rating - band)
    high = min(3500, rating + (band * 3))
    candidates = []
    for p in problems:
        if tag not in p.get("tags", []):
            continue
        p_rating = p.get("rating", 0)
        if not p_rating or not (low <= p_rating <= high):
            continue
        p_id = f"{p.get('contestId', '')}{p.get('index', '')}"
        if p_id in solved_ids:
            continue
        candidates.append(p)
    return random.choice(candidates) if candidates else None


async def _get_cf_problemset() -> list[dict]:
    # Try Redis cache (best-effort — degrades gracefully if Redis is unavailable)
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        try:
            cached = await r.get(CF_PROBLEMSET_CACHE_KEY)
            if cached:
                return json.loads(cached)
        finally:
            await r.aclose()
    except Exception:
        pass

    async with httpx.AsyncClient() as client:
        data = await _cf_get(client, "problemset.problems")
    problems = data["result"]["problems"]

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        try:
            await r.set(CF_PROBLEMSET_CACHE_KEY, json.dumps(problems), ex=CF_PROBLEMSET_TTL)
        finally:
            await r.aclose()
    except Exception:
        pass


async def _trigger_leaderboard_rebuilds(user_id: uuid.UUID, session: AsyncSession) -> None:
    """Enqueue leaderboard rebuilds for all classrooms the user belongs to."""
    from app.workers.classroom_sync import rebuild_classroom_leaderboard

    result = await session.execute(
        select(ClassroomMembership.classroom_id).where(
            ClassroomMembership.user_id == user_id
        )
    )
    for cid in result.scalars().all():
        rebuild_classroom_leaderboard.delay(str(cid))

    return problems
