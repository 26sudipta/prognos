# QA Audit & UX Hardening — 2026-07-01

A full-app bug hunt (auth, handle verification, CF sync, analytics, contests, classrooms,
frontend). Three parallel code reviews produced 26 candidate findings; each was **verified
against the actual code**. 15 were false positives (listed at the bottom); the 11 real
ones are fixed below.

---

## Tier 1 — High (real correctness / business-rule bugs)

### A. Codeforces handle was treated case-sensitively
`backend/app/services/handle.py`. CF handles are case-insensitive, but `initiate_verification`
compared/stored the raw user input (`UserHandle.handle == handle`, `existing.handle == handle`).

**Impact:** two accounts could each "verify" the same CF account as `tourist` vs `Tourist`;
re-initiating with a different case **missed the dormant-row reuse → recreated an orphan row →
re-triggered the blank-dashboard bug**; the lockout counter reset on a case change.

**Fix:** adopt CF's canonical spelling (`cf_user["handle"]` from `fetch_cf_user`) for storage,
and compare case-insensitively (`func.lower(...)` in queries, `.lower()` in Python) in the
uniqueness, supersede, `same_handle`, and dormant-row lookups.

### B. Unverified users could create classrooms
`backend/app/services/classroom.py` `create_classroom` (+ route). No verified-handle check —
the rule "only a verified user can be a teacher" was unenforced server-side, so an unverified
user could create a dataless, broken classroom.

**Fix:** extracted `_require_verified_handle(db, user_id, action)` (used by both `create` and
`join`) → `403` without an active+verified handle. The frontend `createClassroom` now surfaces
the backend detail, so the user sees "Verify your Codeforces handle before creating a classroom."
instead of a generic "Failed to create classroom."

---

## Tier 2 — Medium

### C. Heatmap/streak day misalignment for non-UTC users
`frontend/.../activity-heatmap.tsx` `buildGrid` mixed **local** date math
(`getDate/setDate/getDay`) with **UTC** keys (`toISOString`), while the backend buckets
`daily_activity` by UTC. For users off UTC (e.g. IST) a post-midnight solve landed on the
previous day, making today look empty and the current-streak grace-day logic miscount.

**Fix:** do all grid arithmetic in UTC (`getUTCDate/setUTCDate/getUTCDay`) so cells align with
the UTC keys the API sends. *(Per-user-timezone bucketing remains a future enhancement.)*

---

## Tier 3 — Low / polish

- **E.** Dashboard sync-poll swallowed errors → polled forever on repeated failures. Now stops
  after 5 consecutive errors (`dashboard/page.tsx`), with a shared `stopPoll` cleanup.
- **G.** Verify step: the button stayed enabled after the token countdown hit `00:00` (click →
  410). Now disabled with a "Start over for a fresh one" hint (`handles/page.tsx`).
- **H.** The patient-verify loop now aborts on unmount (via `verifyCancelRef` in a cleanup effect)
  instead of running ~2.5 min after navigation.
- **I.** Recommendation slots that can't be filled (no unsolved problem for a tag) now log a
  `warning` instead of silently producing < 5 (`cf_sync.py`).

---

## Dismissed — verified NOT bugs (do not "fix")

- **Auth restore-vs-redirect race** — `setTokenState` precedes `setIsLoading(false)` in one
  continuation; React 18 batches them, so no `isLoading=false && token=null` render.
- **`scalar_one_or_none` multi-handle crash** (3 reports) — migration 002's partial unique index
  ("one active handle per user per platform") makes >1 active+verified impossible.
- **Submission pagination data loss** — CF `user.status` is sorted by *decreasing* id, so the
  early-break is safe.
- **Heatmap "Sunday off-by-one"** — the Sunday-start anchor is correct.
- **Heatmap cutoff "off-by-one"** — `date.today() - 364 days` already spans 365 inclusive days; it's correct.
- **Refresh-token rotation race** — real but *not worth fixing here*: a `SELECT ... FOR UPDATE` guard
  was prototyped and **reverted** because it makes a second tab's concurrent `/auth/refresh` get a 401
  → bounce to `/login`. The race is already mitigated (httpOnly cookie + single-flight refresh) and
  needs a replayed stolen cookie to exploit; the cure was worse than the disease for multi-tab users.
- **Callback `replaceState`** — intentionally scrubs the token from the URL/history.
- **Hero countdown "drops seconds" at ≥1 day**, **rating-chart empty array** (guarded),
  **join-button spinner lag**, **token-reuse-after-rotation** (correctly rejected),
  **"no attempt consumed on CF network error"** (correct — don't punish a CF outage) — all
  intentional or non-issues.

---

## Verification

- `cd backend && .venv/bin/python -m pytest` — added: cross-case duplicate-claim → 409 and
  case-insensitive dormant reuse (A); `create_classroom` → 403 without a verified handle, 200 with
  (B); existing auth/handle/classroom suites still green (C/D and the `teacher_user` fixture now
  owns a verified handle).
- `cd frontend && npm run build` — 0 TS/ESLint errors.
