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

## Part 1b: Scoring Engine

### What Was Built

```
backend/
├── alembic/versions/
│   └── 012_classroom_league.py       ← NEW (011 → 012): class settings, alias numbers,
│                                       alias counter, classroom_weekly_scores
├── pyproject.toml / uv.lock          ← tzdata (IANA zones inside slim containers)
├── app/
│   ├── models/classroom.py           ← Classroom.timezone/week_starts_on/member_visibility/
│   │                                   alias_seq; ClassroomMembership.alias_no;
│   │                                   NEW ClassroomWeeklyScore
│   ├── services/league_rules.py      ← NEW: pure Growth Points rules, no I/O
│   └── workers/
│       ├── league_sync.py            ← NEW: rebuild_league (gathers inputs, writes rows)
│       └── classroom_sync.py         ← the leaderboard task also rebuilds the league
└── tests/
    ├── unit/test_league_rules.py     ← NEW, 50 tests
    └── integration/test_league_rebuild.py ← NEW, 9 tests
```

### Concepts Explained

#### 1. Pure rules, thin worker

Every number in plan §5 lives in `league_rules.py` as a constant or a pure function: bands,
reference level, week windows, brackets, ranks, and `score_week`. Nothing there touches the
database or reads the clock. That split pays off three ways:

- **Each rule is a one-line unit test.** The band boundaries at −301/−300 or the DST weeks don't
  need a database to check.
- **Tuning is safe.** Change a constant, bump `SCORING_VERSION`, and every new row records which
  rules produced it.
- **The worker stays boring.** `league_sync.py` only gathers inputs with four queries, calls the
  rules, and upserts the results.

#### 2. Four queries per rebuild, whatever the class size

| Query | What it fetches | Why |
|---|---|---|
| Students and handles | user → the **one** active verified handle | Re-verified users have an old inactive handle with the same submissions. Counting both doubled their points, and a test pins this |
| Rating history | (contest, rating after it, time) | Levels, and which contests were rated |
| First solves | `DISTINCT ON (handle, problem)` over individual ACs, left-joined to `cf_problems` | "First-ever" plus difficulty in one pass. Ratings come from the catalogue *now*, so a late CF rating rescores on the next build |
| Participations | Live and virtual submissions grouped per contest | Contest bonuses and upsolve detection |

Team ACs are excluded from the first-solve query entirely, so a later solo solve of a problem
first cracked with a team still scores. Team submissions still count as participation.

#### 3. What freezes, and when it un-freezes

| Value | Frozen when | Why |
|---|---|---|
| `ref_rating` | First build of the week | A Wednesday rating jump must not move the goalposts mid-race |
| `bracket` | First build of the week | Brackets are cut by level, so they freeze with it. Mid-week joiners go to the nearest existing bracket |
| GP, ranks | Never while `live` | Late syncs and late problem ratings keep improving accuracy |
| Everything | `final` | After the grace period the row never changes again |

#### 4. Deviations from the plan, and why

| Plan said | Built | Reason |
|---|---|---|
| Finalize 6 h after the week closes | **48 h** | Many CF rounds run on weekends, and Codeforces rates new problems a day or more after a round. With 6 h, Sunday contest solves would be frozen at the flat "unrated" 2 GP. 48 h lets those ratings arrive, and the UI shows the closed week as "finalizing" until then |
| Alias = max(alias) + 1 at join | A per-class counter, `classrooms.alias_seq` | With max + 1, a newcomer inherits the alias of someone who just left, so "Member 3" silently becomes a different person. The counter only grows. A test pins it |
| Live multiplier on every band | Not on warm-ups | A live 800 problem for a 1600 student isn't contest evidence of anything. Warm-ups stay 1 GP, capped at 10 |
| Solve day needs an AC at Δ ≥ −300 | Unrated solves count too | Gym training is real practice, and it has no CF rating to compare against |
| (unspecified) | A contest counts in the week it **started** | A round running past midnight at the week boundary would otherwise count twice |
| (unspecified) | Upsolve = a practice AC *after* your last contest submission, within 14 days | Practice solves made before a virtual of the same contest are not upsolves |

#### 5. Rebuild triggers on the free tier

There's no broker in production, so the same three triggers as the leaderboard apply. The
read path (`_ensure_league`, Part 1c) rebuilds when the current week has no rows, is older than
10 minutes, is behind a member's newer sync, or holds a week due to finalize. On deployments
with Celery, the existing per-classroom leaderboard task rebuilds the league too. That reuses
one enqueue instead of adding a second `.delay()` per classroom.

#### 6. Timezones need data

`zoneinfo` reads the system timezone database, and `python:3.12-slim` doesn't promise one. The
`tzdata` package is now a direct dependency, so `ZoneInfo("Asia/Dhaka")` works in any container.
`is_valid_timezone()` checks names against what the server can actually load.

## Part 1c: API

### What Was Built

```
backend/app/
├── schemas/classroom.py          ← ClassroomUpdateRequest, ClassroomCreateRequest.timezone,
│                                   ClassroomResponse += timezone/week_starts_on/
│                                   member_visibility, League* response models
├── services/
│   ├── classroom.py              ← _classroom_response, _identity (anonymous mode),
│   │                               update_classroom, 100-member cap, alias at join,
│   │                               league rows removed on leave/remove/delete
│   ├── league.py                 ← NEW: get_league, get_league_history, _ensure_league
│   └── auth.py                   ← account deletion also drops league rows
└── api/v1/routes/classrooms.py   ← PATCH /{id}, GET /{id}/league, GET /{id}/league/history
backend/tests/integration/test_league_api.py   ← NEW, 17 tests
```

| Method and path | Who | Notes |
|---|---|---|
| `GET /classrooms/{id}/league?week=current\|YYYY-MM-DD` | Members | Any date selects its week. A bad value returns 422 |
| `GET /classrooms/{id}/league/history?weeks=8` | Members | `class_median` goes to teachers only |
| `PATCH /classrooms/{id}` | Teacher | `name`, `timezone`, `week_starts_on`, `member_visibility`. Unknown zone or day returns 422 |
| `POST /classrooms` | Verified user | Optional `timezone`, sent from the browser |

### Concepts Explained

#### 7. Students see their own bracket, teachers see the class

| Field | Student | Teacher |
|---|---|---|
| `brackets` | Only their own | All |
| `me` | GP, rank, level, breakdown, 4-week average, best week, next target, ties | `null`, since teachers aren't in the league |
| Entry `ref_rating` | `null` | Shown, so a coach can see levels |
| `pulse` | `null` | Active, median, stretch solves, contests, last week's values, quiet members |
| `suggestions` | 3 recommendations priced in GP for *their* level | Empty |
| History `class_median` | `null` | Shown |

The per-viewer shaping happens on the server, so a curious student can't read other brackets
from the network tab.

#### 8. Anonymous mode masks values, never shapes

`_identity()` decides what a viewer may see of a member, and every endpoint returning classmates
uses it: league, leaderboard and members. In an anonymous class, students see "Member 7" with no
handle or avatar. Teachers and the member themself always see the real identity. Field names and
types never change, since an alias is still a string, and a test pins the old response keys, so
the Android app already on phones keeps parsing. Real user ids stay in responses: both clients
use them only as list keys and for the teacher-only remove action. "Anonymous" hides who
someone is. It doesn't hide how they're doing.

#### 9. API additions from the UI research

The UI research pass asked for a few fields the plan didn't list, so the screen never has to
guess: `tied_with`, `is_me`, `weeks_counted`, `best_week_gp`, a nullable 4-week average, and
`bracket` / `last_active_at` on the quiet-members list.

#### 10. Changing the clock re-cuts the week

A new timezone or week start moves the week boundaries, so `live` rows no longer line up with
any week. `update_classroom` deletes them, and the next read rebuilds on the new boundaries.
`final` rows are history and stay untouched.

#### 11. The member cap is enforced under a lock

Joining now locks the classroom row (`SELECT ... FOR UPDATE`), then checks the 100-member cap and
takes the next alias. Two simultaneous joins can't both see "99 members" or the same alias. The
cap holds until the CF-budget gates (tech-debt D2, D5, D6) land.

### Verification (1b and 1c)

```bash
cd backend
.venv/bin/python -m pytest tests/unit/test_league_rules.py -q            # → 50 passed
.venv/bin/python -m pytest tests/integration/test_league_rebuild.py -q    # → 9 passed
.venv/bin/python -m pytest tests/integration/test_league_api.py -q        # → 17 passed
.venv/bin/python -m pytest -q                                             # → 246 passed
```

### Key Takeaways (1b and 1c)

- **Keep scoring pure.** Rules without I/O are cheap to test, safe to tune, and easy to explain.
- **Freeze inputs, not outputs.** Level and bracket lock for the week. Points keep improving until
  the week finalizes.
- **Pick grace periods from the data's real latency.** CF problem ratings arrive in about a day, not hours.
- **Per-viewer shaping belongs on the server.** Privacy rules enforced in the UI aren't rules.
- **Counters, not maxima, for identifiers that must never be reused.**

---

*Part 1d (web UI) is added below when it lands.*
