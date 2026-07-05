# Phase M2 — Mobile Contests + Offline Cache

**Status:** Built & verified — 2026-07-03. First mobile tab with real data. Feature parity
with the web contests page (list / calendar / detail), backed by an offline SQLite cache.

## What Was Built

The Contests tab: contest window fetched from `GET /contests`, cached in **drift** (SQLite),
rendered **cached-first** (instant from cache, refreshed in the background), fully usable
offline. List (urgency lanes) ⇄ week calendar; platform filter; pull-to-refresh; a periodic
background cache refresh via **workmanager**. No reminders yet — that is M3.

```
mobile/lib/
  core/
    db/app_database.dart              # drift DB: Contests table + replaceContests() (txn)
    db/app_database.g.dart            # generated (build_runner)
    contests/
      contests_api.dart               # GET /contests → drift rows (+ is_stale)
      contests_repository.dart        # cached-first; failed fetch never clears cache
      contests_providers.dart         # riverpod: db, api, repo, notifier, view/filter state
      contest_format.dart             # port of web _lib/contests.ts (colors, grouping, time)
    background/refresh_worker.dart     # workmanager periodic cache refresh (headless, self-auth)
  ui/contests/
    contests_screen.dart              # orchestrator: banner, list⇄week, filter, pull-to-refresh
    widgets/
      next_contest_hero.dart          # featured live/next contest + big countdown
      contest_countdown.dart          # self-ticking countdown w/ web escalation + LIVE pill
      contest_card.dart               # urgency-tinted row
      contest_list_view.dart          # LIVE / TODAY / THIS WEEK / NEXT WEEK / LATER lanes
      contest_calendar_view.dart      # Mon–Sun week grid, week nav
      contest_detail_sheet.dart       # bottom sheet + "Open contest" (url_launcher)
      platform_filter_chips.dart      # client-side multi-select filter
      contest_banner.dart             # offline / stale amber strip
  main.dart                           # + post-first-frame initBackgroundRefresh()

mobile/test/
  support/contests_fakes.dart         # in-memory drift + fake API + sample builder
  contests_repository_test.dart       # cache-replace + offline-preserves-cache
  contests_notifier_test.dart         # airplane-mode state, first-ever offline, fresh load
  contest_format_test.dart            # urgency lanes, local-day grouping, next/duration
  widget_test.dart                    # shell test updated for the real Contests screen

mobile/android/app/src/main/AndroidManifest.xml  # + INTERNET + https VIEW query (url_launcher)
```

## Concepts Explained

### 1. The offline guarantee lives in one rule
The M2 exit criterion is *airplane mode → the full contest list still renders*. Airplane mode
means the `GET /contests` call **throws** (connection error), not "returns empty". So the whole
guarantee reduces to one invariant: **a failed fetch must never propagate to the UI or clear the
cache.** [`ContestsRepository.fetchAndReplace`](../mobile/lib/core/contests/contests_repository.dart)
only writes the cache *after* a successful fetch and otherwise rethrows; the notifier catches and
keeps the last-known-good rows. Two tests pin this down: one asserts a throwing fetch leaves the
cached rows intact, one drives the provider with a down network and asserts the cached window
still resolves.

### 2. Cached-first rendering (no spinner on a screen you've seen)
[`ContestsNotifier.build`](../mobile/lib/core/contests/contests_providers.dart) reads drift first:
if the cache is non-empty it returns those rows **immediately** and kicks off a background refresh
that diff-updates state when it lands. Only a true first-ever visit (empty cache) awaits the
network, and even then a failure degrades to an empty result — never an error screen. Pull-to-
refresh re-fetches without dropping the current view; on failure it keeps what is shown and flips
a `fromCacheOnly` flag that raises the amber "Offline — showing saved contests" banner.

### 3. Timezone: store UTC, group/format in local
Every instant is parsed UTC-aware and stored UTC; presentation converts with `.toLocal()` before
grouping or formatting. Grouping in UTC would silently drop a 23:30-local contest onto the wrong
calendar day for users far from GMT. A dedicated test builds a 23:30-local contest and asserts it
groups under its local day, not the UTC one. All lane/day math is ported 1:1 from the web
`_lib/contests.ts` so mobile and web agree.

### 4. Client-side platform filtering (offline-friendly)
Rather than re-query the server per filter change, M2 fetches the **whole 30-day window** once and
filters platforms **client-side** over the cached rows. Filtering then works offline and needs no
network round-trip, and the filter chips are derived from the distinct platforms already in cache.
The API layer still serializes a `platform` list correctly (`ListFormat.multi` →
`?platform=a&platform=b`, matching FastAPI's `list[str] = Query()`) for when the server filter is
needed — `multiCompatible` would send `platform[]=` and silently break it.

### 5. Background refresh is best-effort, on-open is the guarantee
[`refresh_worker.dart`](../mobile/lib/core/background/refresh_worker.dart) registers a ~8h
workmanager periodic task. It runs in a **headless isolate** with no Riverpod, so it rebuilds auth
from scratch: read the refresh token from the keystore → rotate it via `/auth/refresh/mobile`
(persisting the rotated token, or the next launch's restore breaks) → fetch → replace the cache.
Per the mobile plan, iOS background execution is opportunistic, so the real freshness guarantee is
the on-app-open refresh in the notifier; the periodic task is a top-up. It **only refreshes the
cache** — scheduling notifications is M3.

### 6. The offline path had to be unblocked one layer up (auth gate)
The cached-first screen is only reachable if the user gets *past* `AuthGate`. The original
`restoreSession` cleared the session on **any** error — so a cold launch in airplane mode threw a
connection error, wiped the refresh token, and dropped the user on the login screen (and they had
to re-login even after reconnecting). That silently broke the M2 headline for the
"unopened-for-weeks" case. Fix, in the M1 auth layer: `restoreSession` now distinguishes a
**network error** (keep the session, open with a cached profile persisted in the keystore) from a
genuine **auth rejection** (401/403 → clear and route to login). The `AuthInterceptor` was
hardened the same way — a transient network error during a refresh no longer ends the session.
Three tests pin this: offline restore keeps tokens + returns the cached user; a 401 clears; offline
with no cached profile falls through to login without discarding the token.

### 7. drift needs codegen; lazy list bounds the timers
The `Contests` table's `.g.dart` is generated: `dart run build_runner build` before analyze/test.
Tests use drift's in-memory executor (`NativeDatabase.memory()` via `AppDatabase.forTesting`) so
they never touch `sqlite3_flutter_libs` or the filesystem. The list uses a lazy
`ListView.builder` over a flattened header/card row model, so only on-screen cards build — this
bounds the number of live 1-second countdown timers to roughly the viewport instead of the whole
30-day window (perf: R5).

## Verification

```bash
cd mobile
export PATH="$HOME/dev/flutter/bin:$PATH"
dart run build_runner build            # regenerate app_database.g.dart if the schema changes
flutter analyze                        # No issues found
flutter test                           # 19 passed (was 3)
flutter build apk --debug --dart-define=API_BASE_URL=https://prognos-api.onrender.com
```

- **Offline (headline):** with a seeded cache and the network down, the provider still resolves
  the cached window (`contests_notifier_test.dart`), and a throwing fetch leaves the cache intact
  (`contests_repository_test.dart`). On device: load once online, enable airplane mode, reopen the
  Contests tab → full list renders with the amber offline banner.
- **Grouping:** local-day and urgency-lane classification verified deterministically across
  timezones (`contest_format_test.dart`).
- **Refresh:** pull-to-refresh re-fetches; the ~8h workmanager task tops up the cache in the
  background.

## Key Takeaways
- The offline guarantee is a single invariant — *never let a failed fetch clear or escape the
  cache* — and it must be tested against a **throwing** network, not an empty response.
- Cached-first = read local, render, refresh in the background; spinners only on a never-seen
  screen.
- Store UTC, group/format local — and test the day-boundary case explicitly.
- Background tasks run in a bare isolate: reconstruct auth + DB yourself, and persist rotated
  refresh tokens.

## Next
**M3 — Contest reminders (the star feature):** per-contest bell + per-platform auto-rules, exact
Doze/reboot-proof alarms (Android) and a rolling 64-cap window (iOS), driven by the same drift
cache and a reconcile loop layered onto the M2 workmanager task.
