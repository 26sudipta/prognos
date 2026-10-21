# Phase 6.1: Weekly Growth League (Classroom v2, Slice 1)

> **Goal:** replace the all-time rating table as the classroom's front page with a weekly,
> level-fair race among near peers. Design: `docs/classroom_v2_plan.md` §5 and §10.
>
> **Shipping order.** 1a (data fidelity) changes nothing users can see, so it went to `main`
> right away. That way production starts filling participant types and the problem catalogue
> weeks before the league needs them. 1b to 1d live on `feat/classroom-v2` and merge only after
> the two-week visit baseline from Phase 6.0 is complete.

---

## Part 1a: Data Fidelity

### What Was Built

```
backend/
├── alembic/versions/
│   └── 011_submission_participant_type_cf_problems.py  ← NEW (010 → 011)
├── app/
│   ├── models/
│   │   ├── analytics.py         ← Submission.participant_type, Submission.team_id,
│   │   │                          composite index; NEW CfProblem model
│   │   └── __init__.py          ← CfProblem registered
│   └── workers/
│       └── cf_sync.py           ← ingest keeps author fields; _backfill_participant_types;
│                                  _refresh_cf_problems; both wired into the handle sync
└── tests/integration/
    └── test_data_fidelity.py    ← NEW, 6 tests (Codeforces mocked)
```

### Concepts Explained

#### 1. The league needs two facts the sync used to throw away

Growth Points score a solve by **how far it stretched you** (problem rating minus your level) and
weigh **contest-time solves** above practice ones, since Codeforces allows AI tools in practice.
`user.status` has always returned both facts. `_fetch_submissions` simply didn't keep them:

| Fact | Codeforces field | Before | After |
|---|---|---|---|
| Contest, out of competition, virtual or practice | `author.participantType` | Dropped | `submissions.participant_type` |
| Team submission | `author.teamId` | Dropped | `submissions.team_id` |
| Difficulty | `problem.rating` | Dropped | Joined from `cf_problems` at rebuild time |

#### 2. Join ratings, don't copy them

The obvious move is a `problem_rating` column on `submissions`. It's a trap. Codeforces rates
new problems a few days *after* their round, so every copied rating would need a refresh job, a
backfill and a "rescore later" path.

Instead, `cf_problems` mirrors `problemset.problems`, keyed by `problem_key`, which uses exactly
the format of `submissions.problem_id` (`"1903A"`). The league joins the two when it rebuilds, so a
problem rated on Thursday scores correctly on Thursday's next rebuild with no extra code. Gym
problems aren't in the problemset, so they stay unrated, which the scoring already expects.

#### 3. NULL and UNKNOWN mean different things

Incremental sync stops at the newest stored submission, so rows from before migration 011 would
never get a participant type on their own. `_backfill_participant_types` re-fetches the handle's
full history once and writes the author fields back by `cf_submission_id`.

| Value | Meaning | Who writes it |
|---|---|---|
| `NULL` | Ingested before 011, not backfilled yet | Nobody, after 011 |
| A CF type | The real answer | Ingest, or the backfill |
| `UNKNOWN` | CF no longer returns this submission, or omitted the field | The backfill's last step, or ingest when the field is missing |

Without `UNKNOWN`, a single deleted submission would keep its handle "pending" forever and
trigger a full re-fetch on every sync. Scoring treats `UNKNOWN` exactly like practice.

#### 4. Fetch everything, then write

All Codeforces calls happen before the first `UPDATE`, and the writes run inside one savepoint.
So the failure modes are simple:

| Failure | Result |
|---|---|
| CF errors halfway through the pages | Nothing written. Rows stay NULL and the next sync retries |
| A DB error during the writes | The savepoint rolls back. The sync carries on |
| Success | Every row is typed, the leftovers become UNKNOWN, and the backfill never runs again for that handle |

A partial write would be worse than none: it would mark rows UNKNOWN that a retry could have
resolved.

#### 5. No new cron jobs

Both steps ride the existing handle sync, which cron-job.org already triggers, instead of new
scheduled endpoints:

- **Backfill:** right after new submissions are fetched, and only while the handle still has NULL rows.
- **Catalogue refresh:** after recommendations, at most once every 24 hours. Recommendations
  already load the problemset into memory, so the refresh normally costs **zero** extra CF calls.

Adding cron entries would have needed the production cron secret and someone at the cron-job.org
console. Reusing the sync needs neither, and the CF budget barely moves: one extra history
re-fetch per handle, once.

Both steps are wrapped so they can't fail a sync. The data is "nice to have" today and is only
needed once the league ships.

#### 6. Team submissions are recorded, not credited

ICPC-style team practice puts the same submission under every team member, each with a
`teamId`. Nobody can tell who wrote it, so the league will skip band points for team solves but
still count the contest for everyone (plan §5.3). This phase only records the team id, which
makes that rule possible.

### Verification (1a)

```bash
cd backend
export DATABASE_URL="$(.venv/bin/python -c "from dotenv import dotenv_values; print(dotenv_values('.env')['TEST_DATABASE_URL'])")"
.venv/bin/python -m alembic upgrade head      # → Running upgrade 010 -> 011
.venv/bin/python -m alembic downgrade 010     # → Running downgrade 011 -> 010
.venv/bin/python -m alembic upgrade head
unset DATABASE_URL

.venv/bin/python -m pytest tests/integration/test_data_fidelity.py -q   # → 6 passed
.venv/bin/python -m pytest -q                                          # → 170 passed
```

After deploying, a handle's next sync logs `Backfilled participant_type for N submissions`, and
the first sync of the day logs `Refreshed cf_problems: ~11000 problems`.

### Key Takeaways (1a)

- **Join volatile reference data instead of copying it.** A rating that changes later belongs in
  its own table.
- **Give a backfill a terminal state.** `NULL → value or UNKNOWN` guarantees each row is visited
  once.
- **Do the network part before the database part.** Then a network failure leaves nothing half-written.
- **Ride the schedule you already have.** A daily refresh inside an existing sync beats a new cron
  job nobody can configure.

---

*Parts 1b (scoring engine), 1c (API) and 1d (web UI) are added below as they land.*
