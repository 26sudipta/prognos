# PROGNOS Android App — Implementation Plan
**Status:** SUPERSEDED by `mobile_implementation_plan.md` — the user widened scope to
**Android + iOS**, which broke this doc's Android-native (Kotlin/Compose) premise; the stack is
now Flutter (research-backed, July 2026). The backend-auth design, reminder architecture, and
build-order shape below carry over into the new plan. Kept for the native-Android reasoning.

## Context

PROGNOS today is a FastAPI backend + Next.js web app. The next product is the **Android app**,
positioned as **the main product** — not the thin "companion" the original spec (requirement.md
Module F) describes. It must be **fast to load, lightweight, and have top-notch UI/UX**. The
**reminder system is the headline feature**.

**Decisions made with the user:**
- **Stack:** Native **Kotlin + Jetpack Compose** (chosen over the spec's Flutter — Android-first,
  most reliable exact-alarm/Doze/boot control for reminders, smallest/fastest binary). iOS is a
  separate future project.
- **Scope:** **Full feature parity** with web — auth, dashboard, insights, contests, classrooms,
  handle linking — plus the reminder system.
- **Reminders:** **Favorites/platforms-only** model — default OFF; user stars platforms (e.g.
  Codeforces, AtCoder) or individual contests; only starred contests get reminders. Default lead
  times **1h + 10m** before, configurable in-app.

**Hard constraints from the existing system:**
- Backend is **API-first / read-optimized**; clients only read pre-computed data (preserve this).
- **Timezones:** backend always returns UTC; the app converts to device-local (requirement §7.5).
- **No server push / no FCM** for reminders — all alarm scheduling is **on-device** (zero-cost).
- **Auth gap (blocker):** web auth is a browser-redirect OAuth flow that sets an **httpOnly
  refresh cookie** — a native app cannot use either. A token-based mobile auth path is required
  (see Backend Dependencies). **Security note:** the existing callback decodes Google's ID token
  *without verifying the signature* (safe only because it's a server↔Google exchange, PROGRESS
  1.3). The mobile endpoint receives the ID token **from the device**, so it **must verify the
  signature against Google's public keys and check the audience (client ID)** — copying the
  no-verify pattern would be an auth bypass.

App lives in a new repo dir: **`mobile/android/`** (leaves room for `mobile/ios/` later).

---

## Repository structure — same repo (monorepo)

The Android app lives in the **existing repo** as a third top-level module, matching the
current `backend/` + `frontend/` layout. No separate repo.

```
prognos/
├── backend/          # FastAPI
├── frontend/         # Next.js
├── mobile/
│   └── android/      # ← Android Studio project (its own Gradle root)
│       ├── app/
│       ├── build.gradle.kts
│       └── settings.gradle.kts
└── docs/
```

**Why monorepo:**
- **One source of truth for the API contract** — a backend change and its mobile counterpart
  land in the same commit/PR (e.g. the M1 `/auth/google/mobile` endpoint + the app's auth client).
- **No cross-repo sync overhead** — one `PROGRESS.md`, one `docs/`, one governance file
  (CLAUDE.md) covers the whole product.
- **Matches what already works** — `backend` + `frontend` coexist cleanly; `mobile/android` is
  just another peer.

**Practical notes:**
- The Android project is a **self-contained Gradle build** — open `mobile/android/` directly in
  Android Studio (not the repo root). It does not touch the Python/Node toolchains; they live
  side by side.
- `.gitignore` gains Android entries in M0: `mobile/android/build/`, `.gradle/`,
  `local.properties`, `*.keystore`, `*.jks`, `.cxx/`.
- **When to split later (not now):** only if mobile gets its own team, a conflicting release
  cadence, or a different open-source boundary. Splitting later is cheap; start monorepo.

---

## Tech stack (native, lean by intent)

| Concern | Choice | Why |
|---|---|---|
| Language / UI | Kotlin + **Jetpack Compose + Material 3** | Modern, less boilerplate, top-tier UI control |
| Architecture | **MVVM + unidirectional** (UI → ViewModel `StateFlow` → Repository) | Testable, matches Compose idioms |
| DI | **Hilt** | Standard, compile-time, low overhead |
| Networking | **Retrofit + OkHttp + kotlinx.serialization** | kotlinx is the lightest JSON path; OkHttp `Authenticator` for token refresh |
| Async | **Coroutines + Flow** | |
| Offline cache | **Room (SQLite)** single-source-of-truth for contests; **DataStore** for prefs | Offline-first; spec mandates local contest cache |
| Token storage | **Android Keystore-encrypted** store (EncryptedSharedPreferences / encrypted DataStore) | Refresh token at rest must be encrypted |
| Nav | **Navigation-Compose** (type-safe, kotlinx-serialization routes) | Deep links for join/contest |
| Images | **Coil** | CF avatars; lightweight |
| Charts | **Vico** (rating line chart) + **custom Compose `Canvas`** (heatmap) | Canvas heatmap stays tiny; Vico for the one real chart |
| Background | **WorkManager** (periodic cache refresh) + **AlarmManager** (exact reminder alarms) + boot receiver | The two mechanisms are distinct (see Reminders) |
| Perf | **R8/full mode**, **Baseline Profiles**, **App Startup**, lean deps, Compose stability checks | Makes "fast/light" measurable, not aspirational |

UI direction: dark-first to match the web aesthetic (neutral-dark `#09090C`, indigo accent,
CF rating-color ladder, platform colors), edge-to-edge, predictive back, shimmer skeletons
mirroring the web's `undefined|null|T` loading/empty/data pattern.

---

## Backend dependencies (must ship before/with M1 — small, additive)

In `backend/app/api/v1/routes/auth.py` + `services/auth.py`:
1. **`POST /api/v1/auth/google/mobile`** — body `{ id_token }` from native Google Sign-In.
   **Verify** the ID token via Google's library (`google.auth` / `google-auth`) — signature +
   `aud == GOOGLE_CLIENT_ID` + issuer — then reuse existing `upsert_user`. Returns
   `{ access_token, refresh_token, expires_in }` **in the body** (no cookie).
2. **Mobile refresh transport** — extend `/auth/refresh` (or add `/auth/refresh/mobile`) to read
   the refresh token from the **body/Authorization header** when no cookie is present, rotate it
   (reuse existing `rotate_refresh_token`), and return the new pair in the body.
   Token *format* and rotation/hashing logic are reused as-is; only the **transport** is new.
3. Reuse existing endpoints unchanged for everything else: `GET /users/me`, `/handles*`,
   `/analytics/*`, `/contests*` (already lightweight JSON; defaults to an upcoming window per
   PROGRESS 3.2 — do **not** rely on a `?upcoming=true` param), `/classrooms*`.

---

## Reminder system (the star feature) — design

Two **distinct** mechanisms; the spec's wording merges them — keep them separate:

- **WorkManager** (periodic, every ~6–12h, ≥15min min): only **refreshes the offline contest
  cache** from `GET /contests` and **reconciles alarms** (schedule new starred, cancel
  stale/started). Never fires the reminder itself.
- **AlarmManager**: fires the actual reminder at `contest.start − leadTime`. Use
  **`setAlarmClock()`** — it is exact, wakes from Doze, and is **exempt from the
  `SCHEDULE_EXACT_ALARM` restriction** (denied-by-default on Android 14+), which makes it the
  most reliable choice for a reminder app. A `BroadcastReceiver` posts the notification (deep
  link to the contest).

**Favorites model:** starred platforms + starred contests stored in Room/DataStore. On cache
refresh or favorites change → compute the set of (starredContest × leadTime) → schedule one
`setAlarmClock` per pair with a **stable request code** (hash of contestId+leadTime) so
re-runs are idempotent (no duplicate alarms).

**The parts reminder apps actually get wrong — all handled:**
- **`POST_NOTIFICATIONS`** runtime permission (Android 13+) — request at first reminder opt-in.
- Prefer `setAlarmClock` to sidestep `SCHEDULE_EXACT_ALARM` denial on 12+/14+; if a future
  feature needs `setExactAndAllowWhileIdle`, gate on `canScheduleExactAlarms()` and route the
  user to settings.
- **`BOOT_COMPLETED`** + `TIME_SET`/`TIMEZONE_CHANGED` receiver → **reschedule all alarms**
  (alarms don't survive reboot).
- **Cancellation** when a contest is un-starred, has started, or left the cache.
- Battery-optimization awareness: a one-time, dismissible nudge to exempt the app if the OEM is
  aggressive (Doze handled by `setAlarmClock`, but OEM killers need the hint).

---

## Screen / module map (full parity)

- **Auth:** Google Sign-In (Credential Manager), silent session restore via stored refresh token.
- **Dashboard:** stat strip (streak w/ flame, CF rating in color ladder), activity heatmap
  (Canvas), rating chart (Vico), next-contest countdown.
- **Insights:** tag stats, focus areas (weakness signals), recommendations.
- **Contests:** list + calendar (local TZ), detail, **star** (platform/contest) + reminder
  status; offline from Room.
- **Reminders/Settings:** starred platforms, lead-time config, permission states.
- **Classrooms:** list, detail (leaderboard, cohort analytics, members, invites), **join via
  deep link** (`prognos://join/{token}`), create.
- **Handles:** link + verify CF handle (token-paste flow) — needed for data on a fresh account.
- **Profile/Settings:** account, logout, delete.

---

## Build order (vertical slices — dependency-honest, one at a time)

| Slice | Delivers | Notes |
|---|---|---|
| **M0** | Android Studio project in `mobile/android/`, design system (theme, colors, typography, skeletons), Hilt+Retrofit+Room+WorkManager wiring, perf baseline (R8, App Startup) | Foundation |
| **M1** | **Mobile auth** — backend `/auth/google/mobile` (verified) + body refresh; native Google Sign-In; encrypted token store; OkHttp auto-refresh; session restore | Blocks everything |
| **M2** | **Contests + offline cache** — Retrofit contests API, Room cache, list/calendar/detail UI, WorkManager periodic refresh | Feeds reminders |
| **M3** | **Reminder system** — favorites model, `setAlarmClock` scheduling, notification receiver, permissions, boot/timezone reschedule, alarm reconciliation | ⭐ priority feature; sits on M1+M2 |
| **M4** | **Dashboard + Insights** — analytics endpoints, heatmap (Canvas), rating chart (Vico), tag/weakness/recs | |
| **M5** | **Classrooms + handle linking** — list/detail/leaderboard/cohort/invites, deep-link join, CF handle verify | Completes parity |
| **M6** | **Polish + perf hardening** — Baseline Profiles (Macrobenchmark), Compose stability sweep, accessibility, release signing, Play prep | Makes "fast/light" measured |

Each slice gets a mini-design (screens, API contracts, state) approved before code, and a
`docs/phase_M_X.md` after it passes (CLAUDE.md §5.2).

---

## Verification (per slice + end-to-end)

- **Build/lint:** `./gradlew assembleDebug lint` clean; Compose compiler stability report has no
  unexpected unstable params.
- **Auth (M1):** sign in on a device → backend issues body tokens; kill/reopen app → silent
  restore; force a 401 → OkHttp `Authenticator` refreshes and retries. Verify backend **rejects
  a tampered/expired ID token** (signature + audience check works).
- **Contests/offline (M2):** load contests, enable airplane mode → cached list still renders
  from Room; WorkManager refresh updates the cache.
- **Reminders (M3):** star a platform/contest with a near-future start → reminder fires at
  `start − leadTime` (incl. screen-off/Doze via `setAlarmClock`); reboot the device → alarms
  reschedule from the boot receiver; un-star → alarm cancels; deny `POST_NOTIFICATIONS` → graceful
  prompt.
- **Dashboard/Insights/Classrooms (M4–M5):** data matches web for the same account; deep link
  `prognos://join/{token}` opens the join flow; CF handle verify completes.
- **Perf (M6):** Macrobenchmark cold-start with Baseline Profile shows the improvement; APK size
  tracked; frame timing jank-free on a mid-tier device.

---

## Open decisions to confirm during implementation
- Exact lead-time defaults UI (single set vs per-platform).
- Notification deep-link targets (open contest detail vs registration URL).
- Min SDK (recommend 24/26) vs reminder-API behavior trade-offs.
- Whether handle-verify and classroom-create ship in M5 or defer to a fast-follow.
