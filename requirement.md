# PROGNOS — Master Requirements Document
**Version:** 1.0  
**Status:** In Review — Open items marked `[TBD]`  
**Last Updated:** 2026-06-18  
**Prepared by:** PM / Architect Review Session

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Positioning](#2-product-vision--positioning)
3. [Roles & Personas](#3-roles--personas)
4. [Versioned Roadmap](#4-versioned-roadmap)
5. [User Stories](#5-user-stories)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Data Schema Definitions](#8-data-schema-definitions)
9. [API Contract Expectations](#9-api-contract-expectations)
10. [Data Sync Strategy](#10-data-sync-strategy)
11. [Technology Stack](#11-technology-stack)
12. [Open Questions](#12-open-questions)

---

## 1. Executive Summary

PROGNOS is a **social competitive programming analytics platform** — "Strava for CP." It aggregates fragmented practice data into a unified, actionable dashboard and layers peer accountability on top through a multi-tenant classroom system.

**Core value split:**
- **B2C (Individual):** Unified stats, activity heatmaps, streak tracking, skill-gap detection, and rule-based practice recommendations.
- **B2B / Community (Classrooms):** Transparent peer leaderboards, cohort analytics, and mentor dashboards for universities and bootcamps.

**Architecture philosophy:** API-first. A single FastAPI backend serves both the Next.js web app and the future Flutter mobile app. All frontends are "dumb" — they only read pre-computed data; no aggregation on request.

---

## 2. Product Vision & Positioning

**Tagline:** "The Strava for Competitive Programming."

**Core mechanic:** The transparent classroom leaderboard creates social accountability — seeing a peer's daily streak and tag coverage motivates consistent practice far more effectively than personal dashboards alone.

**Monetization path (deferred, not in V1):**
- **Free:** Individual stats + up to 1 classroom (max 5 members).
- **Premium / B2B:** Unlimited classrooms + advanced cohort analytics for universities and bootcamps.

> V1 ships with no tier enforcement. All users have full access. The schema must be designed to accommodate tier fields later.

---

## 3. Roles & Personas

| Role | How Obtained | Permissions |
|---|---|---|
| **Unverified User** | Registered via Google OAuth, no handle linked | Can view own empty dashboard; cannot join classrooms |
| **Student** | Verified Codeforces handle linked | Full personal dashboard; can join classrooms as a student |
| **Teacher** | Any Student who creates a classroom | All Student permissions + classroom creation + cohort analytics for classrooms they own |

**Multi-role note:** A user can simultaneously be a `teacher` in classroom A and a `student` in classroom B. Role is stored per classroom membership, not globally on the user record.

**[TBD]:** Is "Teacher" a global permission (i.e., must be explicitly granted) or can any Student create a classroom and automatically become its Teacher? Current assumption: any Student can create a classroom — no global Teacher role needed.

---

## 4. Versioned Roadmap

| Version | Scope | Status |
|---|---|---|
| **V1.0** | Google Auth, Handle Verification, Personal Dashboard, Basic Classroom (invite + leaderboard), Contest Discovery | To Build |
| **V1.1** | Skill-gap engine, advanced heatmaps, weakness signals | To Build |
| **V2.0** | Mobile Alpha — contest discovery, offline local alarms, quick-view dashboard | Planned |
| **V3.0** | AI Layer — LLM coaching reading from pre-formatted JSON performance vectors | Planned |

**Out of scope across all versions (until explicitly re-scoped):**
- Email/password authentication
- Comparison Mode (comparing against a specific peer)
- Subscription billing infrastructure
- Cross-platform tag taxonomy mapping
- LeetCode / AtCoder connectors (V3 area)

---

## 5. User Stories

### 5.1 Authentication

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| AUTH-01 | Visitor | Sign in with my Google account | I don't need to manage a separate password |
| AUTH-02 | User | Stay logged in across browser sessions | I don't re-authenticate every visit |
| AUTH-03 | User | Log out from all devices | I can secure my account if needed |
| AUTH-04 | User | See my Google profile picture and name in the UI | The experience feels personalized |

### 5.2 Handle Verification

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| HV-01 | New User | Link my Codeforces handle to my account | My stats are pulled automatically |
| HV-02 | New User | See clear instructions for the 5-step verification process | I know exactly what to do |
| HV-03 | New User | Get feedback if verification fails | I know what went wrong and can retry |
| HV-04 | User | Change my verified Codeforces handle | I can correct mistakes or update it |
| HV-05 | User | See my current sync status | I know if my data is up to date |

### 5.3 Personal Dashboard

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| DASH-01 | Student | See my GitHub-style activity heatmap | I can visualize my practice consistency |
| DASH-02 | Student | See my current and longest streaks | I'm motivated to maintain consistency |
| DASH-03 | Student | See my rating trend over time | I can track long-term improvement |
| DASH-04 | Student | See my solved count and difficulty distribution | I understand my problem-solving profile |
| DASH-05 | Student | See my next upcoming contest with a countdown | I never miss a contest I care about |
| DASH-06 | Unverified User | See an empty state with a clear call to action | I know how to get started |

### 5.4 Analytics & Recommendations

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| AN-01 | Student | See my solved/attempt counts per tag | I understand my topic coverage |
| AN-02 | Student | See which tags I've neglected (14+ days) | I'm reminded to practice forgotten topics |
| AN-03 | Student | See which tags have a low success rate | I know where I keep failing |
| AN-04 | Student | Receive 5 recommended problems per session | I have a structured practice plan |
| AN-05 | Student | See why each problem was recommended | I understand the reasoning behind it |
| AN-06 | Student | Manually trigger a data sync | I can get fresh stats on demand |

### 5.5 Contest Discovery

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| CD-01 | Student | Browse upcoming contests from all major platforms | I have one place to plan my contest calendar |
| CD-02 | Student | Filter contests by platform | I can focus on what I compete in |
| CD-03 | Student | See contests in my local timezone | I don't calculate timezone conversions manually |
| CD-04 | Student | See a calendar view of upcoming contests | I can plan my schedule visually |
| CD-05 | Student | See stale data with a banner if CLIST is down | I still have context even during outages |

### 5.6 Classroom (Teacher)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| CL-01 | Teacher | Create a classroom with a name | I can set up a space for my cohort |
| CL-02 | Teacher | Generate a shareable invite link | My students can join easily |
| CL-03 | Teacher | Revoke an invite link and generate a new one | I can prevent unauthorized joins |
| CL-04 | Teacher | See a leaderboard of all students | I can monitor class-wide progress at a glance |
| CL-05 | Teacher | Remove a student from my classroom | I can manage classroom membership |
| CL-06 | Teacher | See aggregated cohort analytics (weak tags by class average) | I can identify topics to focus my teaching on |
| CL-07 | Teacher | See each student's individual stats | I can give targeted feedback |

### 5.7 Classroom (Student)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| CL-08 | Student | Join a classroom via an invite link | I can participate in structured learning |
| CL-09 | Student | See the classroom leaderboard (all peer stats) | I feel competitive pressure to stay consistent |
| CL-10 | Student | See where I rank vs. my peers | I understand my relative standing |
| CL-11 | Student | Belong to multiple classrooms | I can participate in a university course and a CP club simultaneously |
| CL-12 | Student | Leave a classroom voluntarily | I can exit a classroom I no longer need |

---

## 6. Functional Requirements

### Module A: Authentication & Account Management

#### A.1 Google OAuth Flow
1. User clicks "Sign in with Google."
2. Frontend redirects to Google OAuth consent screen (scopes: `email`, `profile`).
3. Google redirects to `/api/v1/auth/google/callback` with an authorization code.
4. Backend exchanges code for Google ID token; validates token.
5. Backend upserts a `users` record (match on `google_id`).
6. Backend issues:
   - **Access JWT** (15-minute expiry) — returned in JSON response body.
   - **Refresh JWT** (7-day expiry) — set as `httpOnly`, `Secure`, `SameSite=Strict` cookie.
7. Frontend stores access token in memory (never `localStorage`).

#### A.2 Token Refresh
- When an API call returns `401 Unauthorized`, the frontend silently calls `POST /api/v1/auth/refresh`.
- Backend validates the refresh token cookie, issues a new access token and rotates the refresh token.
- If the refresh token is expired or invalid, the user is redirected to the login page.

#### A.3 Logout
- `POST /api/v1/auth/logout` clears the refresh token cookie server-side and invalidates it in the `refresh_tokens` table.
- Multi-device logout: `POST /api/v1/auth/logout-all` invalidates all refresh tokens for the user.

#### A.4 Account Soft-Delete
- `DELETE /api/v1/users/me` marks the user as `is_active = false` and anonymizes PII fields (`email`, `name`, `avatar_url`, `google_id` → replaced with hashed/null values).
- Classroom data and leaderboard cache entries for the deleted user are removed immediately.
- Teacher accounts cannot be deleted in V1. If a user owns one or more classrooms, the delete request returns `409 Conflict` with a message explaining they must delete or transfer their classrooms first. (**Note:** classroom transfer is deferred; the only path in V1 is classroom deletion.)

---

### Module B: Handle Verification Protocol

#### B.1 The 5-Step Verification Flow

**Step 1 — User submits handle:**
- User submits their Codeforces handle via `POST /api/v1/handles/verify/initiate`.
- Backend checks: handle must not already be claimed by another account.
- Backend calls CF API (`https://codeforces.com/api/user.info?handles={handle}`) to confirm the handle exists on Codeforces.
- If valid, backend generates a verification token: a random hex string prefixed `PGS-` (e.g., `PGS-A3F9C2`), stored in `user_handles.verification_token`.
- Token is valid for **30 minutes** from generation time (`verification_token_expires_at`).

**Step 2 — User is shown the token:**
- Frontend displays the token prominently with instructions: "Paste this exact string into your Codeforces profile's About/Summary section."

**Step 3 — User updates their CF profile:**
- This step is performed manually by the user on codeforces.com.

**Step 4 — User triggers verification check:**
- User clicks "I've done it — verify now" → `POST /api/v1/handles/verify/confirm`.
- Backend calls CF API: `user.info` endpoint, reads the `lastName` field where the user pasted the token.
- Backend string-matches the token against the profile data.

**Step 5 — Handle permanently linked:**
- On match: `user_handles.is_verified = true`, `verified_at = now()`, `verification_token = null`.
- On no match: increment `verification_attempt_count`. Return error with remaining attempts.

#### B.2 Retry & Lockout Policy
- Max **5** verification attempts per token (attempt counter on `user_handles`).
- On 5th failed attempt: `is_locked = true`, `lockout_expires_at = now() + 1 hour`.
- After lockout expires, user can generate a new token and start fresh (attempt counter resets).
- A user can regenerate a new token (and reset the flow) at any time before lockout, but the old token is immediately invalidated.

#### B.3 Token Expiry Handling
- If the 30-minute token window expires before confirmation, the user must re-initiate with `POST /api/v1/handles/verify/initiate` again (generates a fresh token).
- The user is not penalized — expiry does not count against the 5-attempt limit.

#### B.4 Handle Already Claimed
- If another account already has `handle = X` with `is_verified = true`, the request is rejected with `409 Conflict`.
- If another account has `handle = X` with `is_verified = false` (pending), the new request supersedes it (old unverified record is cleared).

#### B.5 Changing a Verified Handle
- User can unlink their current handle and begin a new verification for a different handle.
- On unlink: `user_handles` record is soft-deleted (marked `is_active = false`); all associated submissions, tag_stats, rating_history, weakness_signals, and recommendation_sets are **retained** (historical data preserved).
- New handle goes through the full 5-step flow.

#### B.6 CF Account Suspended/Deleted Post-Verification
- If a CF API call for a previously verified handle returns a 404 or banned status, the handle is marked `status = 'suspended'` in `user_handles`.
- Suspended handles are excluded from live sync but their historical data remains visible in the UI with a "Handle unavailable" banner.

---

### Module C: Multi-Tenant Classroom System

#### C.1 Classroom Lifecycle

```
Created → [Invite links active] → Members joining → Active → [Teacher deletes] → Deleted
```

- Any verified user can create a classroom (becomes its Teacher automatically).
- A classroom must have at least 1 member (the Teacher) to exist.
- Deleting a classroom removes all membership records and leaderboard cache entries.
- **Teacher account deletion is blocked in V1** if the user owns classrooms (see A.4).

#### C.2 Invite Links

- Generated by Teacher: `POST /api/v1/classrooms/{id}/invites`.
- Format: `https://prognos.app/join/{token}` where token is a cryptographically random 32-character URL-safe string.
- **Multi-use:** a single invite link can be used by any number of students.
- **Expiry:** 7 days from generation. After expiry, the link returns `410 Gone`.
- Teacher can revoke an active link at any time: `DELETE /api/v1/classrooms/{id}/invites/{invite_id}`. Revoking does **not** remove students who already joined via that link.
- Teacher can generate multiple active invite links simultaneously. **[TBD]:** Is there a maximum number of active links per classroom?

#### C.3 Joining a Classroom

1. Student visits invite URL; frontend calls `POST /api/v1/classrooms/join` with the token.
2. Backend validates: token exists, not expired, not revoked.
3. Backend checks: student is not already a member.
4. Student must have a verified handle to join. If unverified, return `403 Forbidden` with message: "Verify your Codeforces handle before joining a classroom."
5. A `classroom_memberships` record is created with `role = 'student'`.
6. At join time, the student implicitly consents to transparent leaderboard visibility. **No opt-out exists after joining.**
7. Student's data is added to the classroom leaderboard cache on the next scheduled refresh (within 1–2 hours).

#### C.4 Transparency Rules

The following data is **always visible to all classroom members** (students and teachers):
- Activity heatmap (daily activity counts)
- Current streak and longest streak
- Total solved count
- Solved count by difficulty bracket
- CF rating (current + trend)
- Tag-wise solved counts and last-active timestamps
- Weakness signals (neglected + low-success tags)

The following data visibility is **[TBD]:**
- Specific problem names and submission history (the roadmap lists this as "optional" — not yet decided)

#### C.5 Leaderboard

- **Primary sort:** CF rating (descending).
- **[TBD]:** Secondary sort when ratings are equal (last_active? solved_count? streak?).
- Leaderboard data is served entirely from the `classroom_leaderboard` precomputed cache table.
- Never aggregated from raw submissions on request.
- Cache refresh: every **1–2 hours** via Celery scheduled task.

#### C.6 Student Removal

- Teacher calls `DELETE /api/v1/classrooms/{id}/members/{user_id}`.
- The student's `classroom_memberships` record is deleted immediately.
- The student's row is removed from `classroom_leaderboard` immediately.
- The student's personal analytics data (submissions, tag_stats, etc.) is **not** affected — it belongs to the student's account, not the classroom.

#### C.7 Student Self-Exit

- Student calls `DELETE /api/v1/classrooms/{id}/members/me`.
- Same effect as teacher removal — membership and leaderboard entry deleted.
- Student's personal data unaffected.

#### C.8 Cohort Analytics (Teacher View)

- Teacher can access aggregated stats for their entire cohort:
  - Class average rating
  - Most neglected tags across all students (ranked by frequency)
  - Tags with lowest average success rate across all students
  - Student attendance (days active in last 30 days, descending)
- This view is computed from the same `classroom_leaderboard` cache, not raw data.

---

### Module D: Analytics Engine

#### D.1 Activity Heatmap

- Data source: `daily_activity` table.
- Each cell = number of submissions on that UTC day.
- Intensity levels (exact thresholds `[TBD]`):
  - `0` = no activity (gray)
  - `1–2` = low (light green)
  - `3–5` = medium (medium green)
  - `6–9` = high (dark green)
  - `10+` = very high (deepest green)
- Timezone conversion: performed client-side using the browser's local timezone.

#### D.2 Streak Calculation

- **Active day:** a day where `daily_activity.count > 0`.
- **Current streak:** consecutive active days ending on today (UTC) or yesterday (to avoid penalizing users who haven't submitted yet today).
- **Longest streak:** maximum consecutive active day sequence in the user's history.
- Stored in a derived field; recomputed after every sync.

#### D.3 Skill Matrix

Computed per `user_handle`, per tag:

| Metric | Definition |
|---|---|
| `solved_count` | Number of distinct problems where at least one submission was `OK` (Accepted) |
| `attempt_count` | Total submissions for problems under this tag |
| `acceptance_rate` | `solved_count / distinct_problems_attempted` |
| `last_activity_at` | Timestamp of the most recent submission (any verdict) under this tag |
| `failure_profile` | Count of verdicts by type: WA, TLE, MLE, RE, etc. |

A problem can belong to multiple tags — it is counted under each tag independently.

#### D.4 Weakness Detection (Rule-Based)

Three signal types:

**Signal 1 — Neglected Tag:**
- Condition: `last_activity_at < now() - 14 days` AND `solved_count >= 1` (must have solved at least once to be "neglected," not just "never attempted").
- Score: days since last activity (higher = worse).
- Label: `"Neglected — {X} days since last practice"`

**Signal 2 — Low Success Tag:**
- Condition: `attempt_count >= 5` AND `acceptance_rate < 0.50`.
- Score: `1 - acceptance_rate` (lower rate = higher score).
- Label: `"Low success — {X}% acceptance rate"`

**Signal 3 — Under-Practiced Tag:**
- Condition: `solved_count < 5` AND tag appears in problems at the user's difficulty level (i.e., the tag is relevant, not just obscure).
- Score: `5 - solved_count` (fewer solved = higher score).
- Label: `"Under-practiced — only {X} problems solved"`

**Output format for each signal:**
```json
{
  "tag": "dynamic programming",
  "signal_type": "neglected",
  "score": 23.0,
  "reason": "Neglected — 23 days since last practice",
  "computed_at": "2026-06-18T10:00:00Z"
}
```

**[TBD]:** When the same tag triggers multiple signal types, are they reported as separate entries or merged into one with a combined score?

#### D.5 Rule-Based Recommendations

**Inputs:** Top weak/neglected tags from weakness signals + user's current CF rating.

**Algorithm:**
1. Rank weakness signals by score (descending). Take top 5 distinct tags.
2. For each tag, determine the target difficulty bracket (see below).
3. Query CF problem database (cached locally): filter by tag + difficulty bracket + exclude already-solved problems.
4. Pick 1 problem per tag (total: up to 5 problems).

**Difficulty Band Determination:**
- Target band = [`user_rating - 100`, `user_rating + 300`].
- Clamped to CF's range: minimum 800, maximum 3500.
- Example: user rated 1400 → target band [1300, 1700].
- **[TBD]:** Exact band ranges per tier need confirmation. The above formula is a recommended starting point.

**Recommendation output per problem:**
```json
{
  "problem_id": "1234A",
  "problem_name": "Divisibility",
  "tag": "math",
  "difficulty": 1400,
  "url": "https://codeforces.com/problemset/problem/1234/A",
  "reason": "Low success on math — 32% acceptance. Practice at your level (1400)."
}
```

**Fallback:** If no problem is found for a tag at the target band, expand the band by ±200 and retry once. If still empty, skip that tag and move to the next ranked signal.

**Regeneration:** User can regenerate recommendations manually. Same 30-minute manual sync cooldown does **not** apply to recommendation regeneration — this is a local computation, no external API calls.

#### D.6 Rating Trend

- Source: `rating_history` table.
- One record per rated contest participation.
- Displayed as a time-series line chart.
- X-axis: contest date; Y-axis: rating after that contest.

---

### Module E: Contest Discovery

#### E.1 Data Source

- **CLIST API** (clist.by — free tier, registration required).
- CLIST aggregates contests from Codeforces, LeetCode, AtCoder, CodeChef, HackerRank, and others.
- Contest data is fetched globally and cached in the `contests` table — it is **not** per-user.

#### E.2 Sync Schedule

- A Celery beat task runs every **3–6 hours** to fetch upcoming contests from CLIST.
- Fetches contests within a rolling window (now → now + 30 days). **[TBD]:** Exact lookahead window.
- Upserts into `contests` table (match on `clist_id`).

#### E.3 Filtering

Users can filter the contest list by:
- Platform (Codeforces, LeetCode, AtCoder, CodeChef, etc. — whatever CLIST returns)
- Time range (today, this week, this month)

**[TBD]:** Are platform filter options hardcoded or dynamically derived from distinct platform values in the DB?

#### E.4 Timezone

- All contest timestamps stored in UTC in the database.
- Conversion to local time is performed **exclusively on the client side** using the browser's Intl API or the `date-fns-tz` / `Luxon` library.
- The backend never returns localized times.

#### E.5 Stale Data Handling

- If the CLIST sync fails, the UI displays the most recently cached contest data with a banner: "Contest data may be outdated — last synced {relative_time_ago}."
- The `contests` table includes a `last_synced_at` metadata field to power this banner.

#### E.6 Calendar View

- Displays contests in a week/month grid.
- Platform-color-coded entries.
- Clicking a contest shows: name, platform, start time (local), end time (local), duration, and a link to the registration/contest page.

---

### Module F: Mobile Companion (V2.0 — Scope Definition)

> This module is **not** built in V1. Defined here to ensure V1 API and schema decisions do not block V2 development.

#### F.1 Core Mobile Features
- Quick-view dashboard (heatmap thumbnail, current streak, next contest countdown).
- Contest discovery with local device alarms (no FCM, no server-side push).
- Offline contest cache using SQLite embedded in the Flutter app.

#### F.2 Zero-Cost Notification Strategy
- On app launch (or background fetch), the mobile app calls `GET /api/v1/contests?upcoming=true`.
- Upcoming contests are stored in local SQLite.
- Flutter's `flutter_local_notifications` + `workmanager` schedule OS-level alarms for each contest.
- **No server push required** — all alarm scheduling is done on-device.
- Background fetch interval: **[TBD]** — recommended every 6–12 hours.

#### F.3 V1 API Compatibility Requirements
- All API responses must be valid JSON (no Next.js-specific patterns).
- Contest endpoint must support lightweight queries (only fields needed for mobile cache).
- Auth tokens issued in V1 must be usable by the mobile app (same JWT standard).

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Metric | Target |
|---|---|
| Dashboard page load (first meaningful paint) | < 2 seconds |
| Leaderboard load (pre-computed cache read) | < 500ms |
| Analytics endpoint response time | < 300ms (cached data) |
| API p99 latency | < 1 second under normal load |

- The frontend **never** triggers raw data aggregation. All reads are from pre-computed derived tables.
- Heavy computation (syncing, analytics recompute) is pushed to Celery workers asynchronously.

### 7.2 Scalability

- **Single classroom sync (100 students):** CF API rate limit = 1 request per ~2 seconds. Minimum sync time for 100 students = ~3.3 minutes. This is background work — acceptable.
- **Celery worker concurrency:** `[TBD]` — must be tuned to CF rate limits. Recommended: 1 concurrent CF API worker per classroom sync to prevent rate limit violations.
- **Classroom leaderboard:** served from `classroom_leaderboard` materialized/cache table. No joins or aggregations on the hot path.
- **Contest data:** single global cache, served identically to all users. No per-user contest computation.

### 7.3 Security

| Concern | Implementation |
|---|---|
| Authentication | Google OAuth 2.0 only — no passwords stored |
| Access tokens | Short-lived JWT (15 min), signed with server secret |
| Refresh tokens | Long-lived (7 days), `httpOnly` + `Secure` cookie, stored hashed in DB |
| API keys (CF, CLIST) | Stored server-side in environment variables, never exposed to clients |
| Handle verification | Token generation uses `secrets.token_urlsafe()` — cryptographically random |
| Rate limiting | Sync endpoints: 1 manual sync per 30 minutes per user. Handle verification: 5 attempts per token window. Auth endpoints: `[TBD]` — recommend 10 requests/minute per IP. |
| CORS | `[TBD]` — restrict to known frontend origins in production |
| Input validation | All request bodies validated via Pydantic before processing |
| SQL injection | Use SQLAlchemy ORM with parameterized queries — no raw SQL string interpolation |

### 7.4 Reliability

- External API calls (CF, CLIST) must use: timeouts (recommended: 10 seconds), retries (3 attempts), and exponential backoff (1s → 2s → 4s).
- All sync jobs record their status in `user_handles.sync_status` (`idle` | `in_progress` | `completed` | `sync_error`).
- Classroom sync partial failure: failed students are marked `sync_error` and retried in the next scheduled cycle. The rest of the classroom sync completes normally.
- Graceful degradation: if CF API is unavailable, the UI shows the last-synced data with a "Sync unavailable" status indicator.

### 7.5 Timezone Policy

- **Database:** All timestamps stored in `TIMESTAMPTZ` (UTC).
- **Backend:** Never converts timestamps to local time.
- **Frontend:** Converts UTC to local time using browser's `Intl.DateTimeFormat` API or `date-fns-tz`.
- **Mobile:** Same client-side conversion using the device's system locale.

### 7.6 API Design Rules

- All endpoints return `application/json`.
- No Next.js Server Actions for core data fetching — pure REST.
- Versioned prefix: `/api/v1/`.
- HTTP status codes used semantically (200, 201, 204, 400, 401, 403, 404, 409, 410, 422, 429, 500).
- Error responses follow a consistent envelope:
  ```json
  { "detail": "Human-readable error message", "code": "MACHINE_READABLE_CODE" }
  ```

---

## 8. Data Schema Definitions

> Field types use PostgreSQL conventions. All `id` fields are `UUID` with default `gen_random_uuid()`. All tables have `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` and `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` unless otherwise stated.

### 8.1 `users`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | From Google profile |
| `google_id` | VARCHAR(255) | UNIQUE, NOT NULL | Google `sub` field |
| `name` | VARCHAR(255) | NOT NULL | Google display name |
| `avatar_url` | TEXT | NULLABLE | Google profile picture URL |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | false = soft-deleted |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

> `[TBD]` Future: add `tier ENUM('free','premium') DEFAULT 'free'` when monetization ships.

### 8.2 `refresh_tokens`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `token_hash` | VARCHAR(255) | UNIQUE, NOT NULL | SHA-256 hash of the token |
| `expires_at` | TIMESTAMPTZ | NOT NULL | now() + 7 days |
| `revoked_at` | TIMESTAMPTZ | NULLABLE | Set on logout/rotation |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

### 8.3 `user_handles`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `platform` | ENUM('codeforces') | NOT NULL | Extensible for future platforms |
| `handle` | VARCHAR(255) | NOT NULL | |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT false | |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | false = unlinked |
| `status` | ENUM('active','suspended') | NOT NULL, DEFAULT 'active' | |
| `verification_token` | VARCHAR(50) | NULLABLE | Cleared after verification |
| `verification_token_expires_at` | TIMESTAMPTZ | NULLABLE | |
| `verification_attempt_count` | INT | NOT NULL, DEFAULT 0 | |
| `is_locked` | BOOLEAN | NOT NULL, DEFAULT false | |
| `lockout_expires_at` | TIMESTAMPTZ | NULLABLE | |
| `verified_at` | TIMESTAMPTZ | NULLABLE | |
| `sync_status` | ENUM('idle','in_progress','completed','sync_error') | NOT NULL, DEFAULT 'idle' | |
| `last_synced_at` | TIMESTAMPTZ | NULLABLE | |
| `last_sync_error` | TEXT | NULLABLE | Error message if sync_error |
| `last_manual_sync_at` | TIMESTAMPTZ | NULLABLE | For 30-min cooldown enforcement |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

> Unique constraint: `(user_id, platform, is_active)` — one active handle per platform per user.

### 8.4 `contests`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `clist_id` | BIGINT | UNIQUE, NOT NULL | CLIST's internal ID for upsert |
| `platform` | VARCHAR(100) | NOT NULL | As returned by CLIST (e.g., "codeforces.com") |
| `name` | VARCHAR(500) | NOT NULL | |
| `start_time` | TIMESTAMPTZ | NOT NULL | UTC |
| `end_time` | TIMESTAMPTZ | NOT NULL | UTC |
| `duration_seconds` | INT | NOT NULL | |
| `url` | TEXT | NOT NULL | Registration/contest link |
| `last_synced_at` | TIMESTAMPTZ | NOT NULL | When this record was last updated from CLIST |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

### 8.5 `submissions`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_handle_id` | UUID | FK → user_handles.id, NOT NULL | |
| `cf_submission_id` | BIGINT | NOT NULL | CF's submission ID |
| `problem_id` | VARCHAR(50) | NOT NULL | e.g., "1234A" |
| `problem_name` | VARCHAR(500) | NOT NULL | |
| `verdict` | VARCHAR(50) | NOT NULL | "OK", "WRONG_ANSWER", "TIME_LIMIT_EXCEEDED", etc. |
| `programming_language` | VARCHAR(100) | NULLABLE | |
| `time_consumed_millis` | INT | NULLABLE | |
| `memory_consumed_bytes` | INT | NULLABLE | |
| `submitted_at` | TIMESTAMPTZ | NOT NULL | UTC, from CF data |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

> Unique constraint: `(user_handle_id, cf_submission_id)`.  
> Index on: `(user_handle_id, submitted_at DESC)` for incremental sync.

### 8.6 `submission_tags`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `submission_id` | UUID | FK → submissions.id, NOT NULL | |
| `tag` | VARCHAR(100) | NOT NULL | CF tag as-is (e.g., "dynamic programming") |

> A problem with N tags creates N rows here.

### 8.7 `daily_activity`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_handle_id` | UUID | FK → user_handles.id, NOT NULL | |
| `activity_date` | DATE | NOT NULL | UTC date |
| `submission_count` | INT | NOT NULL, DEFAULT 0 | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

> Unique constraint: `(user_handle_id, activity_date)`.

### 8.8 `tag_stats`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_handle_id` | UUID | FK → user_handles.id, NOT NULL | |
| `tag` | VARCHAR(100) | NOT NULL | |
| `solved_count` | INT | NOT NULL, DEFAULT 0 | Distinct accepted problems |
| `attempt_count` | INT | NOT NULL, DEFAULT 0 | Total submissions under this tag |
| `distinct_problems_attempted` | INT | NOT NULL, DEFAULT 0 | Denominator for acceptance_rate |
| `acceptance_rate` | NUMERIC(5,4) | NULLABLE | solved / distinct_attempted |
| `wa_count` | INT | NOT NULL, DEFAULT 0 | Wrong Answer submissions |
| `tle_count` | INT | NOT NULL, DEFAULT 0 | Time Limit Exceeded |
| `mle_count` | INT | NOT NULL, DEFAULT 0 | Memory Limit Exceeded |
| `re_count` | INT | NOT NULL, DEFAULT 0 | Runtime Error |
| `last_activity_at` | TIMESTAMPTZ | NULLABLE | Most recent submission under this tag |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

> Unique constraint: `(user_handle_id, tag)`.

### 8.9 `rating_history`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_handle_id` | UUID | FK → user_handles.id, NOT NULL | |
| `cf_contest_id` | INT | NOT NULL | CF's contest ID |
| `contest_name` | VARCHAR(500) | NOT NULL | |
| `rank` | INT | NULLABLE | User's rank in the contest |
| `old_rating` | INT | NOT NULL | |
| `new_rating` | INT | NOT NULL | |
| `delta` | INT | NOT NULL | new_rating - old_rating |
| `contest_time` | TIMESTAMPTZ | NOT NULL | UTC |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

> Unique constraint: `(user_handle_id, cf_contest_id)`.

### 8.10 `weakness_signals`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_handle_id` | UUID | FK → user_handles.id, NOT NULL | |
| `tag` | VARCHAR(100) | NOT NULL | |
| `signal_type` | ENUM('neglected','low_success','under_practiced') | NOT NULL | |
| `score` | NUMERIC(10,4) | NOT NULL | Higher = more severe |
| `reason` | TEXT | NOT NULL | Human-readable label |
| `computed_at` | TIMESTAMPTZ | NOT NULL | |

> Unique constraint: `(user_handle_id, tag, signal_type)` — upserted on each sync.

### 8.11 `recommendation_sets`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `generated_at` | TIMESTAMPTZ | NOT NULL | |

### 8.12 `recommendations`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `recommendation_set_id` | UUID | FK → recommendation_sets.id, NOT NULL | |
| `problem_id` | VARCHAR(50) | NOT NULL | e.g., "1234A" |
| `problem_name` | VARCHAR(500) | NOT NULL | |
| `tag` | VARCHAR(100) | NOT NULL | The weakness tag this addresses |
| `difficulty` | INT | NULLABLE | CF difficulty rating |
| `url` | TEXT | NOT NULL | Direct link to problem |
| `reason` | TEXT | NOT NULL | Explanation for the recommendation |
| `position` | INT | NOT NULL | 1–5, display order |

### 8.13 `classrooms`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `name` | VARCHAR(255) | NOT NULL | |
| `owner_id` | UUID | FK → users.id, NOT NULL | The Teacher |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | false = deleted |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

### 8.14 `classroom_invites`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `classroom_id` | UUID | FK → classrooms.id, NOT NULL | |
| `token` | VARCHAR(64) | UNIQUE, NOT NULL | URL-safe random token |
| `created_by` | UUID | FK → users.id, NOT NULL | Teacher who generated it |
| `expires_at` | TIMESTAMPTZ | NOT NULL | created_at + 7 days |
| `revoked_at` | TIMESTAMPTZ | NULLABLE | Set when teacher revokes |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

### 8.15 `classroom_memberships`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `classroom_id` | UUID | FK → classrooms.id, NOT NULL | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `role` | ENUM('teacher','student') | NOT NULL | |
| `invite_id` | UUID | FK → classroom_invites.id, NULLABLE | Which invite was used (NULL for Teacher/creator) |
| `joined_at` | TIMESTAMPTZ | NOT NULL | |

> Unique constraint: `(classroom_id, user_id)`.

### 8.16 `classroom_leaderboard`

Precomputed cache. Rebuilt every 1–2 hours by Celery task.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `classroom_id` | UUID | FK → classrooms.id, NOT NULL | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `cf_handle` | VARCHAR(255) | NOT NULL | Denormalized for display |
| `user_name` | VARCHAR(255) | NOT NULL | Denormalized |
| `avatar_url` | TEXT | NULLABLE | Denormalized |
| `cf_rating` | INT | NULLABLE | Current CF rating |
| `solved_count` | INT | NOT NULL, DEFAULT 0 | |
| `current_streak` | INT | NOT NULL, DEFAULT 0 | |
| `longest_streak` | INT | NOT NULL, DEFAULT 0 | |
| `last_active_at` | TIMESTAMPTZ | NULLABLE | |
| `top_tags` | JSONB | NULLABLE | Top 5 solved tags and counts |
| `weak_tags` | JSONB | NULLABLE | Top 3 weakness signals |
| `computed_at` | TIMESTAMPTZ | NOT NULL | |

> Unique constraint: `(classroom_id, user_id)`.

---

## 9. API Contract Expectations

> All routes require `Authorization: Bearer <access_token>` unless marked `[PUBLIC]`.  
> Base prefix: `/api/v1`

### 9.1 Auth Routes

| Method | Path | Description |
|---|---|---|
| GET | `/auth/google` | Redirect to Google OAuth consent screen [PUBLIC] |
| GET | `/auth/google/callback` | Handle OAuth callback, issue tokens [PUBLIC] |
| POST | `/auth/refresh` | Rotate refresh token, issue new access token [COOKIE] |
| POST | `/auth/logout` | Revoke current refresh token |
| POST | `/auth/logout-all` | Revoke all refresh tokens for the user |

**`GET /auth/google/callback` response (success):**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "name": "Sudipta Das",
    "email": "user@example.com",
    "avatar_url": "https://..."
  }
}
```

### 9.2 User Routes

| Method | Path | Description |
|---|---|---|
| GET | `/users/me` | Get current user profile |
| PATCH | `/users/me` | Update display name |
| DELETE | `/users/me` | Soft-delete account |

### 9.3 Handle Routes

| Method | Path | Description |
|---|---|---|
| GET | `/handles` | List user's handles and sync status |
| POST | `/handles/verify/initiate` | Start verification; returns token |
| POST | `/handles/verify/confirm` | Confirm token pasted; checks CF API |
| POST | `/handles/{id}/sync` | Manually trigger a sync (30-min cooldown) |
| DELETE | `/handles/{id}` | Unlink a verified handle |

**`POST /handles/verify/initiate` request:**
```json
{ "platform": "codeforces", "handle": "tourist" }
```

**`POST /handles/verify/initiate` response (201):**
```json
{
  "handle_id": "uuid",
  "verification_token": "PGS-A3F9C2",
  "expires_at": "2026-06-18T10:30:00Z",
  "instructions": "Paste 'PGS-A3F9C2' into the Last Name field of your Codeforces profile (codeforces.com/settings/social)."
}
```

### 9.4 Analytics Routes

| Method | Path | Description |
|---|---|---|
| GET | `/analytics/dashboard` | Heatmap, streaks, rating summary |
| GET | `/analytics/tags` | Full tag stats (skill matrix) |
| GET | `/analytics/weakness` | Current weakness signals |
| GET | `/analytics/recommendations` | Latest recommendation set |
| POST | `/analytics/recommendations/refresh` | Regenerate recommendations |
| GET | `/analytics/rating-history` | Rating trend data points |

### 9.5 Contest Routes

| Method | Path | Description |
|---|---|---|
| GET | `/contests` | Upcoming contests (with filters) |
| GET | `/contests/calendar` | Contests in calendar format |

**`GET /contests` query params:**
- `platform` (optional, repeatable): filter by platform name
- `from` (optional): ISO date string, default = now
- `to` (optional): ISO date string, default = now + 30 days
- `limit` / `offset`: pagination

### 9.6 Classroom Routes

| Method | Path | Description |
|---|---|---|
| GET | `/classrooms` | List classrooms the user belongs to |
| POST | `/classrooms` | Create a classroom (user becomes Teacher) |
| GET | `/classrooms/{id}` | Get classroom details |
| DELETE | `/classrooms/{id}` | Delete classroom (Teacher only) |
| GET | `/classrooms/{id}/leaderboard` | Get leaderboard (from cache) |
| GET | `/classrooms/{id}/cohort` | Get cohort analytics (Teacher only) |
| GET | `/classrooms/{id}/members` | List members |
| DELETE | `/classrooms/{id}/members/{user_id}` | Remove a student (Teacher only) |
| DELETE | `/classrooms/{id}/members/me` | Student self-exit |
| POST | `/classrooms/join` | Join via invite token |
| POST | `/classrooms/{id}/invites` | Generate invite link (Teacher only) |
| GET | `/classrooms/{id}/invites` | List active invites (Teacher only) |
| DELETE | `/classrooms/{id}/invites/{invite_id}` | Revoke invite (Teacher only) |

---

## 10. Data Sync Strategy

### 10.1 Codeforces User Sync

**Trigger types:**
1. **On handle verification** — full historical sync (all submissions, all rating changes).
2. **Scheduled daily sync** — Celery beat task runs once per day for all verified, active handles.
3. **Manual sync** — user-triggered, throttled to once per 30 minutes.

**Incremental sync logic:**
- Fetch submissions where `submissionId > last_known_cf_submission_id` (derived from max `cf_submission_id` in `submissions` table for this handle).
- If no prior submissions exist: fetch full history (paginated, all pages).

**Rate limit compliance:**
- CF API allows ~1 request/second unofficially. System enforces a **2-second delay** between requests to be safe.
- Celery worker for CF sync: configured with concurrency **1 per classroom sync job** to prevent rate limit violations from parallel classroom syncs.
- `[TBD]` — Global CF API request rate cap across all Celery workers.

**Post-sync recomputation:**
After every successful sync, the worker triggers (in order):
1. Recompute `daily_activity` for affected days.
2. Recompute `tag_stats`.
3. Recompute `rating_history` (incremental, new contests only).
4. Recompute `weakness_signals`.
5. Regenerate `recommendation_sets` (latest only).
6. Update `classroom_leaderboard` for any classroom the user belongs to.

### 10.2 CLIST Contest Sync

- Celery beat task: every 3–6 hours. `[TBD]` — Exact interval needs decision.
- Fetches contests from CLIST for the next 30 days.
- Upserts into `contests` on `clist_id`.
- Records `last_synced_at` on a global metadata record or a dedicated `sync_metadata` table.
- No user-specific work — one global sync for all users.

### 10.3 Classroom Leaderboard Rebuild

- Celery beat task: every 1–2 hours. `[TBD]` — Exact interval.
- For each active classroom:
  1. Fetch all active members.
  2. Read latest derived data for each member from `tag_stats`, `daily_activity`, `rating_history`, `weakness_signals`.
  3. Upsert `classroom_leaderboard` rows.
- Partial failure handling: if data for a student is unavailable (sync_error), their leaderboard row is preserved from the previous cache run (stale but not removed).

---

## 11. Technology Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| **Web Frontend** | Next.js (TypeScript) | App Router recommended |
| **UI Components** | shadcn/ui + Tailwind CSS | |
| **Charts** | Recharts or Chart.js | `[TBD]` — pick one |
| **Date handling** | date-fns + date-fns-tz | or Luxon — `[TBD]` |
| **Backend API** | FastAPI (Python) | |
| **Data validation** | Pydantic v2 | Schema-first: define models before routes |
| **ORM** | SQLAlchemy 2.x | Async mode with `asyncpg` driver |
| **Migrations** | Alembic | |
| **Auth** | Python `python-jose` (JWT) + Google OAuth client | |
| **Database** | PostgreSQL 15+ | |
| **Task queue** | Celery | |
| **Message broker** | Redis | Used by Celery |
| **Mobile (V2)** | Flutter | `flutter_local_notifications`, `workmanager` |
| **Deployment** | `[TBD]` | |
| **CI/CD** | `[TBD]` | |

---

## 12. Open Questions

The following items remain undefined and must be answered before the relevant module can be implemented. They are grouped by implementation priority.

### P0 — Blocks V1.0 implementation

| # | Question | Blocked Module |
|---|---|---|
| ~~OQ-01~~ | ~~Which field for verification token?~~ **Resolved: `lastName` field.** | Handle Verification (B) |
| OQ-02 | What are the exact CORS allowed origins for production? (e.g., `https://prognos.app`) | Auth (A) |
| OQ-03 | What is the production domain? Needed for OAuth redirect URI registration in Google Cloud Console. | Auth (A) |
| OQ-04 | What is the Celery concurrency configuration for CF API workers? Must not exceed CF rate limits across simultaneous classroom syncs. | Sync (10) |

### P1 — Blocks V1.1 implementation

| # | Question | Blocked Module |
|---|---|---|
| OQ-05 | Are platform filter options for contests hardcoded (predefined list) or dynamically derived from distinct values in the DB? | Contest Discovery (E) |
| OQ-06 | When the same tag triggers multiple weakness signal types (e.g., both "neglected" and "low_success"), are they reported as separate entries or merged into one combined signal? | Weakness Engine (D) |
| OQ-07 | What is the exact lookahead window for CLIST contest fetching? (e.g., 30 days, 60 days) | Contest Sync (10.2) |
| OQ-08 | What is the exact interval for the classroom leaderboard rebuild task? (1 hour or 2 hours?) | Classroom (C) |
| OQ-09 | What are the intensity level thresholds for the activity heatmap? (e.g., 0, 1-2, 3-5, 6-9, 10+) | Analytics (D) |
| OQ-10 | What is the secondary leaderboard sort key when two students have the same CF rating? | Classroom (C) |
| OQ-11 | Is there a maximum number of active invite links per classroom? | Classroom (C) |
| OQ-12 | Are specific problem names and submission history visible to classroom peers, or only aggregate stats? (Roadmap marks this "optional".) | Classroom (C) |

### P2 — Blocks V2.0 (Mobile)

| # | Question | Blocked Module |
|---|---|---|
| OQ-13 | What is the background fetch interval for the Flutter mobile app? | Mobile (F) |
| OQ-14 | What deployment infrastructure will be used (VPS, Railway, Fly.io, AWS, GCP)? | Infra |
| OQ-15 | What is the rate-limiting threshold for auth endpoints (login/callback)? | Auth (A) |

### P3 — Future / Business

| # | Question | Notes |
|---|---|---|
| OQ-16 | Is there a separate "admin" role for universities to manage multiple teachers under one B2B account? | Needed before Premium tier design |
| OQ-17 | Can a user's solve history be exported (CSV, JSON)? | Possible V1.1 feature |
| OQ-18 | What are the exact CF difficulty bands for recommendations? The formula `[user_rating - 100, user_rating + 300]` is proposed but not yet confirmed. | Recommendations (D) |
| OQ-19 | What is the exact CLIST sync interval (3 hours, 6 hours, or configurable)? | Contest Sync (10.2) |
