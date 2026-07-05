# Phase M5 — Classrooms + Handle Verification

**Status:** Built & verified — 2026-07-04. Two features: Codeforces handle verification (which
unlocks the M4 dashboard with live data) and the full classroom system with invite deep links.

## What Was Built

### Part A — Handle verification
A 3-step wizard (enter handle → copy the `PGS-XXXX` token into your CF *Organization* field → verify)
driven by a state machine restored from `GET /handles`. On success it invalidates the analytics
provider so the dashboard fills in. Reached from the M4 no-handle nudge.

### Part B — Classrooms (the "Classes" tab)
Classroom list (cached-first), create, join-by-code, and a detail screen with a leaderboard
(CF-coloured), members, and — for teachers — cohort analytics and invite management, plus a bulk
sync. Invite **deep links** (`prognos://join/{token}`) open a join screen from a cold launch or
while running.

```
mobile/lib/
  core/handles/
    handle_models.dart          # Handle, HandleInitiation, ConfirmException(kind, attempts)
    handles_api.dart            # list/initiate/confirm/unlink; maps 400/423/410 → typed errors
    handles_providers.dart      # HandleController: None→Pending→Verified/Failed/Locked state machine
  core/classrooms/
    classroom_models.dart       # Classroom/Leaderboard (cached, toJson) + members/cohort/invites/preview
    classrooms_api.dart         # every /classrooms/* call
    classrooms_repository.dart  # cached-first list + leaderboard (drift KV blobs)
    classrooms_providers.dart   # list notifier, leaderboard family, members/cohort/invites, syncClassroom()
  ui/handles/handle_verify_screen.dart
  ui/classrooms/
    classrooms_screen.dart      # list + Create + Join (Classes tab)
    classroom_detail_screen.dart# tabs: Leaderboard / Members / Cohort / Invites; sync; leave/delete
    join_screen.dart            # prognos://join/{token} → preview → join
  ui/shell/home_shell.dart      # Classes tab; app_links deep-link routing
  ui/dashboard/dashboard_screen.dart  # no-handle nudge → verify wizard
  core/db/app_database.dart     # clearUserData also wipes classrooms.* on sign-out

mobile/android/app/src/main/AndroidManifest.xml  # prognos:// VIEW intent-filter
mobile/ios/Runner/Info.plist                     # CFBundleURLTypes: prognos scheme

mobile/test/  handle_controller_test · classrooms_repository_test (+ shell/clear-user-data updated)
```

## Concepts Explained

### 1. The confirm state machine maps HTTP codes to states, not exceptions
`POST /handles/verify/confirm` asks the server to re-check the CF Organization field. The API layer
translates its status codes into a typed `ConfirmException` (`400` mismatch + `attempts_remaining`,
`423` locked, `410` expired) so the controller — not the UI — decides the next state. A mismatch
with attempts left stays `Pending` (showing the count); `0` left or `423` re-derives from
`GET /handles` into `Locked`; `410` drops to `None` with "token expired". The whole flow restores
across an app reopen because `build()` derives state from `GET /handles` (which carries the pending
token and lockout).

### 2. Verification unlocks the dashboard by invalidation
On a successful confirm the controller calls `ref.invalidate(analyticsProvider)`. The dashboard's
`has_verified_handle` flips on the next fetch and the nudge is replaced by real analytics — no manual
refresh, no cross-screen coupling beyond one invalidation.

### 3. Classrooms reuse the cached-first pattern; leaderboard is network-first-cache-fallback
The classroom **list** is a full cached-first notifier (instant from drift, background refresh) like
M2/M4. The **leaderboard** is a `FutureProvider.family` that fetches fresh online and falls back to
the drift cache offline — Riverpod 3's non-codegen family *AsyncNotifier* argument access is awkward,
and network-first-with-fallback still satisfies "works offline" without that friction. Polling while
a bulk sync runs is driven by the tab widget invalidating the provider every 5s.

### 4. Deep links: one handler, two delivery paths
`prognos://join/{token}` is registered via an Android `VIEW` intent-filter and an iOS
`CFBundleURLTypes` entry. `app_links` delivers both the **cold-launch** URI (`getInitialLink`) and
**while-running** URIs (`uriLinkStream`); a single `_handleDeepLink` parses `host == 'join'` +
first path segment and pushes the join screen. The join screen previews the class via the public
`join-preview` endpoint before committing.

### 5. Sign-out now also wipes classroom cache
Classroom membership/leaderboard is per-user, so `clearUserData` was extended to delete the
`classrooms.*` cache keys alongside analytics and reminders (the M4 privacy fix). The public
contests cache is still kept. A test asserts the classroom cache is cleared on sign-out.

## Verification

```bash
cd mobile
export PATH="$HOME/dev/flutter/bin:$PATH"
flutter analyze                        # No issues found
flutter test                           # 52 passed (was 41)
flutter build apk --release --dart-define=API_BASE_URL=https://prognos-api.onrender.com
```

- **Handle state machine** unit-tested end-to-end: none/verified/pending/locked derivation, initiate,
  confirm success, confirm mismatch (keeps pending + attempts), confirm lockout (re-derives to locked).
- **Classrooms:** model JSON round-trip (classroom + leaderboard incl. tags/is_me), list cache
  round-trip, and leaderboard offline cache fallback.
- **Sign-out** clears the classroom cache (extended privacy test).
- **Emulator smoke checks** (same rigour as M3's R8 catch): (1) the release APK **installs and
  launches to the login screen** — `app_links` + the new `VIEW` intent-filter don't crash under R8;
  (2) `adb am start -a VIEW -d prognos://join/testtoken` resolves to `MainActivity` with `Status:
  ok`, proving the scheme + intent-filter + delivery are wired. Full route-to-JoinScreen needs auth
  (HomeShell mounted), which is the OAuth-gated part.
- **Sign-out privacy completeness:** `signOut` invalidates *every* per-user in-memory provider —
  analytics, reminders, **and `classroomsListProvider`** (added this slice) — not just the drift
  cache, since a non-autoDispose provider outlives `clearUserData`. A comment marks the list so M6
  extensions don't reintroduce the leak.

## Key Takeaways
- Map transport errors to domain states at the API boundary; the UI should never see a `DioException`.
- One `ref.invalidate` is the clean seam between "handle verified" and "dashboard shows data".
- Riverpod 3 non-codegen family *notifiers* are awkward; a `FutureProvider.family` with cache
  fallback + widget-driven polling is the pragmatic equivalent.
- Deep links need both the cold-launch and while-running APIs, plus the native scheme declarations on
  both platforms.

## Next
**M6 — Widget + polish + release:** Android home-screen widget, perf/accessibility hardening, store
listings, Shorebird, signed release builds.
