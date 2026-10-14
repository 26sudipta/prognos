# Uptime Runbook — Keeping `prognos-api` Running

**Written:** 2026-10-14, during the outage that took the API down.
**Status:** **RESOLVED** — root cause found and proven, service verified back up the same day.
**Scope:** why the backend went down, how it was fixed, and how to stop it recurring.

---

## 0. Root cause (proven)

> **The deployed image could not resolve the database's own migration revision, so the
> container died at boot on every single start.**

`backend/.env` points `DATABASE_URL` at **production Neon**. Running `alembic upgrade head`
locally while building commit `613333e` therefore stamped **production** at revision `009`.
That commit was then **never pushed** — `git reflog` shows `origin/main` went
`f292be3 → d150cfb`, and `d150cfb` ships migrations **001–008 only**.

So production's *schema* moved ahead of production's *code*. Every container start then ran:

```
alembic upgrade head
  → reads alembic_version from the DB  → '009'
  → looks for revision '009' in its own versions/ dir  → only 001-008 present
  → CommandError: Can't locate revision identified by '009'
  → exit non-zero
  → `&&` short-circuits, uvicorn NEVER STARTS, container dies
```

Reproduced offline against the exact deployed tree, no database involved:

```
$ git ls-tree --name-only d150cfb backend/alembic/versions/   # 8 files, 001..008
heads known to the deployed image: ['008']
resolve '008': OK -> 008
resolve '009': *** CommandError: Can't locate revision identified by '009'
```

This explains every observation: a registered hostname with no healthy instance, an
indefinite hang rather than a 503, a perfectly healthy database, code that works fine
locally, and a three-month outage that never self-healed — because every restart hit the
same unresolvable revision.

**The fix that worked:** pushing the commits. The image now contains revision `009`, so
`alembic upgrade head` resolves it and is a clean no-op. Verified at 2026-10-14 —
`/api/v1/health` `200` in 3.0 s, `/api/v1/ready` `200` with `"database":"ok"`, the Vercel
proxy `200`, and unsigned cron calls still `401`. The §6 entrypoint change independently
prevents a repeat: uvicorn now starts even when migrations fail.

### Correction to an earlier reading

An intermediate diagnosis treated `alembic_version = 009` as proof that *a container had
booted and migrated successfully*, and so ruled the deployed code out. That was wrong: the
stamp came from a **laptop**, not from a container. The instance-hour arithmetic in §3 is a
real and separate hazard, but it was **not** what took the service down.

---

## 1. Evidence gathered during triage

Measured from this machine on 2026-10-14, not inferred:

| Component | State | Evidence |
|---|---|---|
| Frontend (Vercel) | **Healthy** | `GET https://prognos-chi.vercel.app` → `200` in 0.9 s |
| Database (Neon) | **Healthy** | Connects in ~2 s, `server_version 18.6`, **726 users, 332 contests** intact |
| Migrations | **Fully applied** | `alembic_version = 009`; `refresh_tokens` has `rotated_at` + `replaced_by_id` |
| Backend (Render) | **DOWN** | TLS completes, then **zero bytes for 180 s** |
| Cron jobs | **Stopped** | A *symptom*, not the cause — see §5 |

### The backend failure is "no instance", not "bad code"

This is the key diagnostic, and it rules out the obvious suspects.

A Render hostname that does not exist answers **fast**:

```
$ curl -I https://prognos-api-does-not-exist-zz99.onrender.com/
HTTP/2 404
x-render-routing: no-server      ← 10 seconds
```

Our hostname does something different — it accepts the TLS handshake, negotiates
HTTP/2, and then **never sends a single byte**, even after 180 seconds:

```
$ curl --max-time 180 https://prognos-api.onrender.com/api/v1/health
curl: (28) Operation timed out after 180002 ms with 0 bytes received
```

So the service is **still registered** in Render's router (otherwise we would get
the `no-server` 404), but Render has **no healthy instance to route to** and holds
the request at the edge instead of answering.

### What this rules out

Three theories were tested and **disproved**:

1. ~~**"Migration 009 broke the deploy."**~~ **This was half right, and the half that was
   wrong mattered.** Migration 009 *was* involved — but not because it failed. It was never
   deployed at all (`613333e` was never pushed), while the *database* was already stamped
   at 009 from a local run. The mismatch, not the migration, is the cause. See §0.
2. **"Multiple alembic heads."** The chain is linear `001 → 009`, single head.
3. **"Neon is IPv6-only and Render can't reach it."** Neon is dual-stack — it
   publishes both `A` (`13.251.17.193`, …) and `AAAA` records.

A cold start also does not explain it: Render's documented spin-up is **~1 minute**,
and four separate requests across 180 s failed to wake it.

---

## 2. Restoring it (kept for reference — already done)

> Resolved by §0: pushing the hardened commits rebuilt the image with revision 009 present.
> The steps below are what to do if the service is ever down for a *different* reason.

### If it happens again: check the dashboard

Everything above was measurable from outside. The remaining question — *why* there is
no instance — is only visible from inside Render, and there is no API token on this
machine. **Open the Render dashboard and grab three things:**

1. **Service status badge** — `prognos-api` → is it *Suspended*, *Failed*, or *Live*?
2. **Events / Logs tab** — the last deploy's outcome and final log lines.
3. **Billing → Usage** — free instance-hours consumed this cycle, and the cycle's start date.

### Step 0: the hardening is already on `main` — done

The §6 fixes landed in **`2a4b89e`** (`fix(deploy): retry boot migrations, add readiness
probe`) and were pushed, so `autoDeploy` has the hardened image. This mattered for ordering:
before that commit, `HEAD` was `613333e` — the build containing the `&&` bug — and
"Deploy latest commit" would have redeployed the *unhardened* image.

If the service is suspended, the triggered deploy will not land until you resume it, which is
harmless. If it is live-but-wedged, the push alone may have fixed it.

The status badge then decides the fix:

| Status | Meaning | Fix |
|---|---|---|
| **Suspended** | Free instance-hours exhausted | Resume; then §4 so it stops recurring |
| **Deploy failed** | Container never became healthy | Read logs; `Manual Deploy → Deploy latest commit` |
| **Live** but hanging | Wedged instance | `Manual Deploy → Clear build cache & deploy` |

---

## 3. Why this keeps happening: the instance-hour math

This is the part that matters, and it is arithmetic rather than a guess.

Render's free tier, per [their docs](https://render.com/docs/free):

- **750 instance-hours per month**, per **workspace** (not per service)
- Shared across *all* free web services in the workspace
- Exhaust them and Render **suspends every free web service until the 1st of next month**
- Services spin down after **15 minutes** without inbound traffic; spin-up takes **~1 minute**

The keep-warm ping from the original go-live plan fires **every 10 minutes, 24/7**. Ten
minutes is *below* the 15-minute idle threshold, which is the whole point — the service
never idles. But that also means it is billed for **every hour of every day**:

| Month length | Hours consumed | Headroom vs 750 |
|---|---|---|
| 28 days (Feb) | 672 h | 78 h |
| 30 days | 720 h | 30 h |
| **31 days** | **744 h** | **6 h (0.8 %)** |

**Seven months a year have 31 days** (Jan, Mar, May, Jul, Aug, Oct, Dec). In those months
the current setup runs within **1 %** of a cap that, when crossed, takes the service down
until the 1st. A couple of redeploys — each one running a new instance while the old one
drains — is enough to cross it. That is a recurring outage built into the configuration.

### One honest caveat about this month

An hours suspension **resets on the 1st**. A single always-on service could only have
burned ~324 h by 14 October, which is nowhere near 750 — and you confirmed `prognos-api`
is the only free service in the workspace. So **hours alone do not explain why it is
still down today**; that is what the Billing → Usage page in §2 settles. Either way the
math above is a live hazard that needs fixing, which is what §4 does.

Render's docs name one other suspension trigger worth knowing about: exceeding a
**service-initiated outbound traffic threshold**. PROGNOS continuously calls the
Codeforces and CLIST APIs, so if Usage shows hours well under 750, check for a
notice about outbound traffic.

---

## 4. The plan: 24/7 uptime without tripping the cap

You want it up all the time. Here is the honest trade-off.

### Option A — recommended free setup: a 22-hour ping window

Ping every 10 minutes **except 02:00–04:00** local. The service sleeps for that one
quiet window and is awake every other minute of the day.

| | Value |
|---|---|
| Awake per day | 22 h + ~15 min idle tail ≈ **22.25 h** |
| Worst month (31 d) | **~690 h** |
| Headroom | **~60 h (8 %)** |
| Cost | **$0** |
| Trade-off | One ~60 s cold start for the first visitor between 02:00 and 04:00 |

That 8 % headroom absorbs redeploys and restarts, which 0.8 % does not.

### Option B — guaranteed always-on: Render Starter, $7/month

The free tier **cannot** guarantee what you are asking for. Starter removes the entire
problem class: no spin-down, no instance-hour cap, no keep-warm job at all, no cold
starts, and it fixes the latent `BackgroundTasks` issue in §6. If the API being up at
03:00 genuinely matters, this is the only answer that holds.

**Recommendation:** do Option A now (free, ~10 minutes of setup). Move to Option B when
PROGNOS has users who would notice a 3 a.m. cold start.

### Setting up Option A on cron-job.org

Use the account that already has the three disabled jobs. Set each job's **timezone to
`Asia/Dhaka`** so the window means local time.

| Job | URL (POST/GET) | Schedule (cron) | Header |
|---|---|---|---|
| Keep-warm | `GET /api/v1/health` | `*/10 0-1,4-23 * * *` | — |
| Sync contests | `POST /api/v1/cron/sync-contests` | `0 0,4,8,12,16,20 * * *` | `X-Cron-Secret` |
| Sync handles | `POST /api/v1/cron/sync-handles` | `0 0,6,12,18 * * *` | `X-Cron-Secret` |

Why those hour lists:

- `0-1,4-23` is 22 hours — it **omits hours 2 and 3**, creating the 02:00–04:00 gap.
- The sync jobs fire on 4-hour and 6-hour boundaries that **all fall outside** the gap,
  so neither one wakes the service during the window and spoils the savings.
- Keep-warm points at `/api/v1/health`, which does **no database I/O** (see §6). Never
  point keep-warm at `/ready` — it would hit Neon 144 times a day for no reason.

**On each job, turn on failure notifications** (cron-job.org → job → *Notifications* →
email on failure). Do this before anything else; it is what converts the next outage
from three silent months into an email.

### Monthly habit

Around the **25th**, check Render → Billing → Usage. Under ~600 h means the window is
working. Near 750 means something is pinging outside the window.

---

## 5. Why the cron jobs "stopped"

They are a **consequence**, not a cause. cron-job.org **automatically disables a job after
repeated consecutive failures**. The sequence was:

```
backend goes down
  → every 10-minute keep-warm ping fails
  → cron-job.org disables the job after N consecutive failures
  → the 4 h / 6 h sync jobs fail and get disabled too
  → nothing pings, nothing syncs, nobody is told
```

So **re-enabling the cron jobs will not fix the API** — they will just fail again until
the Render service is back. Order matters: **restore Render first (§2), then re-enable
the three jobs (§4).**

This is also the root cause of the *duration*. The outage itself might have been a
one-hour blip; it lasted because every channel that could have reported it was
configured to fail silently. Hence the failure notifications in §4.

---

## 6. Hardening shipped alongside this runbook

These are cause-independent — worth having whatever the dashboard says.

### `backend/docker-entrypoint.sh` (new) — migrations can no longer brick the container

Before, the Docker `CMD` was:

```dockerfile
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

The `&&` is the bug. Neon's free compute **scales to zero**, so a container booting while
Neon is still waking can fail to connect. One transient failure meant `alembic` exited
non-zero, `&&` short-circuited, **uvicorn never started**, and the container died — which
on a free service can leave exactly the "registered but no healthy instance" state seen
in §1. A redeploy was the only way out.

Now migrations are **retried with exponential backoff** (5 attempts, 5 s → 80 s), and the
server starts **either way**. Verified against a stub `alembic` that fails twice and then
succeeds, and against one that always fails:

```sh
if alembic upgrade head; then break; fi
# ... after the last attempt:
echo "[entrypoint] WARNING: migrations failed after $ATTEMPTS attempts; starting server anyway"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

The Dockerfile invokes it as `CMD ["sh", "./docker-entrypoint.sh"]` rather than relying on
the executable bit surviving the `COPY` — a "permission denied" at boot would reproduce the
very no-healthy-instance state the script exists to prevent.

Starting unmigrated is deliberate. A reachable API that reports its own broken state is
far easier to diagnose than a service with no instance and no logs — and in the common
case (a connection blip, not a bad migration) the schema is already correct anyway.

### `/api/v1/ready` (new) — readiness, kept off the health check path

Two probes, on purpose:

| Endpoint | Touches DB? | Used by |
|---|---|---|
| `/api/v1/health` | **No** | Render `healthCheckPath`, keep-warm ping |
| `/api/v1/ready` | **Yes** (`SELECT 1`) | Humans, uptime monitors; `503` when DB is unreachable |

`/health` **must** stay dependency-free. It is Render's `healthCheckPath`, so if it
touched a sleeping Neon the first probe after a deploy could fail and Render would mark
the deploy failed — the probe would *cause* outages instead of reporting them. That
invariant is pinned by `test_health_does_not_touch_the_database`, which swaps in a dead
engine and asserts `/health` still returns `200`.

### Latent issue, logged not fixed

The cron endpoints return `202` immediately and run the real work in FastAPI
`BackgroundTasks`. On a service that can spin down, a long `sync-handles` run (sequential
over every verified handle, rate-limited to be polite to Codeforces) **can be reaped
mid-flight** when the instance stops. The keep-warm ping masks this most of the time. It
is a genuine design limit of the worker-free deployment, not today's outage. Option B
(always-on) or a real worker removes it.

### Region mismatch, documented not fixed

`render.yaml` says `region: singapore`, but the live origin resolves to
`gcp-us-west1-1.origin.onrender.com`. Render only honors `region` **when the service is
first created**, so the change in `a805e8c` never took effect. Every query crosses the
Pacific to Neon in `ap-southeast-1`. Editing the YAML does nothing — fixing it means
deleting and recreating the service, which is a separate decision from restoring it.

---

## 6b. The underlying hazard: tests and migrations pointed at production

§0 showed the outage was caused by a **local** `alembic upgrade head` reaching the
**production** database. The same wiring had a second, quieter effect.

`backend/.env` sets `DATABASE_URL` to production Neon, and the suite built its engine
straight from `settings.DATABASE_URL`. So every `pytest` run created rows in production.
By 2026-10-14 that had accumulated:

| | Before | After cleanup |
|---|---|---|
| Users | 762 (**747** `@test.com`) | **15** (all real) |
| Classrooms | 726 (**724** test-owned) | **2** (both real) |
| Invites | 348 | 2 |
| Memberships | 704 | 4 |
| `user_handles` | 563 | 14 |

Leakage was dated `2026-06-30` (220), `07-01` (116), `07-02` (340), `07-13` (35) and
`10-14` (36) — the last batch from this session's own verification run.

**Cleanup performed** (backed up to JSON first, then one transaction): test-created invites,
then test-owned classrooms, then the test users. `classrooms.owner_id` and
`classroom_invites.created_by` are `ON DELETE NO ACTION`, so that order matters — a plain
`DELETE FROM users` fails. Checked first that **no real user** held a membership or
leaderboard row in a test-owned classroom (both zero), then verified seven orphan classes
afterwards: all clean, `alembic_version` still `009`, contests and all 4018 submissions
untouched.

### The guard

`tests/conftest.py` now resolves `TEST_DATABASE_URL` first and **aborts collection** if the
resolved host is not local:

```
RuntimeError:
Refusing to run the test suite against a non-local database.
  resolved host : ep-sweet-forest-ao5l5nla.c-2.ap-southeast-1.aws.neon.tech
  database      : prognos
If you truly mean to target a remote database, set ALLOW_REMOTE_TEST_DB=1.
```

Two details make it actually airtight rather than decorative:

- The check runs **before any `app.*` import** and writes the result back into
  `os.environ["DATABASE_URL"]`. `app.core.config` builds its `Settings` singleton at import
  time and env vars outrank the `.env` file, so this redirects the **application** engine
  too — which is what `TestClient` and `/ready` use. Guarding only the fixtures would have
  left that path still pointed at production.
- The one stray `create_async_engine(settings.DATABASE_URL)` in
  `test_clist_sync_integration.py` was rerouted through the same guarded URL.

`ALLOW_REMOTE_TEST_DB=1` remains as a deliberate override. Nothing in CI should set it.

### Result

| | Against prod Neon | Against local `prognos_test` |
|---|---|---|
| Suite | 157 passed in **343 s** | 157 passed in **7.45 s** |
| Rows written to production | 36 users, 34 handles | **0** |

A 46x speedup was an unplanned bonus: the old runtime was almost entirely round-trips to
Singapore.

**Still open (minor):** the fixtures leak. A clean run left 35 users and 34 classrooms behind
in the test database — the same cleanup gap that filled production, now harmlessly local. Worth
a follow-up to wrap fixtures in a rollback or truncate between runs.

### Also recommended

`alembic upgrade head` run locally still targets whatever `DATABASE_URL` says, which is
production. That is the exact command that caused the outage. Production migrations run in
the container (Dockerfile `CMD`), so a local run should essentially never target Neon —
consider pointing `DATABASE_URL` at local Postgres for day-to-day work and keeping the
production URL in a separate, deliberately-sourced file.

---

## 7. Verification

After resuming the service in Render:

```bash
# 1. Liveness — expect 200 fast once an instance is up
curl -sS -w '\n%{http_code} in %{time_total}s\n' \
  https://prognos-api.onrender.com/api/v1/health
# → {"status":"ok","service":"prognos-api"}

# 2. Readiness — proves the API can actually reach Neon
curl -sS -w '\n%{http_code}\n' \
  https://prognos-api.onrender.com/api/v1/ready
# → {"status":"ok","service":"prognos-api","database":"ok"}  200

# 3. Same-origin proxy through Vercel (the path the browser really uses)
curl -sS https://prognos-chi.vercel.app/api/v1/ready

# 4. Cron auth still rejects unsigned calls
curl -sS -o /dev/null -w '%{http_code}\n' -X POST \
  https://prognos-api.onrender.com/api/v1/cron/sync-contests
# → 401
```

Then in cron-job.org, hit **"Execute now"** on each of the three jobs and confirm
`200`/`202`.

Local test suite:

```bash
cd backend && .venv/bin/python -m pytest tests/integration/test_health_routes.py -q
# → 4 passed
```

---

## 8. Key takeaways

- **The backend is the only broken piece.** Neon, all 726 users, and all migrations are
  intact. Nothing needs restoring from backup.
- **The deployed code is fine.** `alembic_version = 009` proves a container booted and
  migrated successfully; this is an infrastructure state problem.
- **A 10-minute keep-warm on Render free consumes 744 of 750 hours in a 31-day month.**
  That 0.8 % headroom is the recurring outage. A 22-hour window brings it to 8 %.
- **The cron jobs stopping is a symptom.** cron-job.org disables jobs that keep failing,
  so restore Render *before* re-enabling them.
- **Silence was the real failure.** Nothing was configured to report the outage. Failure
  notifications are the highest-value five minutes of this entire runbook.
- **Free tier cannot guarantee 24/7.** Option A gets ~22 h/day safely; only Starter
  ($7/mo) actually guarantees always-on.

---

## Next

Restore the service per §2, re-enable the three cron jobs with failure notifications per
§4, then decide Option A vs Option B.
