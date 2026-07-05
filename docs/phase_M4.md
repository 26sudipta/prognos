# Phase M4 — Mobile Dashboard + Insights

**Status:** Built & verified — 2026-07-03. Personal analytics on mobile, cached-first, matching the
web for the same account. (Live data needs a verified handle — verification arrives on mobile in
M5; until then the tab shows a "link handle on web" nudge.)

## What Was Built

The Dashboard tab, with an **Overview ⇄ Insights** toggle:
- **Overview** — stat strip (streak / solved / rating / peak, CF colour ladder), a Canvas activity
  heatmap, and an `fl_chart` rating chart.
- **Insights** — tag bars, Focus Areas (weakness signals), and refreshable recommendations.

All six `/analytics/*` endpoints are cached in drift and rendered cached-first; the tab polls while
the backend reports `is_syncing`, and works offline from cache.

```
mobile/lib/
  core/analytics/
    analytics_models.dart        # port of _lib/analytics.ts — fromJson + toJson (cache round-trip)
    analytics_api.dart           # 6 typed calls over the authed Dio
    analytics_repository.dart     # cached-first; blobs in the drift Settings KV table
    analytics_providers.dart      # AsyncNotifier (cache→fetch→poll-while-syncing) + view toggle
  ui/dashboard/
    dashboard_screen.dart         # orchestrator: toggle, offline/sync notes, no-handle nudge, pull-to-refresh
    widgets/
      stat_strip.dart             # 2×2 stat cards
      activity_heatmap.dart       # CustomPainter, 53×7, 5 levels, tap-for-day
      rating_chart.dart           # fl_chart area chart, [min−50,max+50], touch tooltip
      tag_stats.dart              # top-15 bars
      focus_areas.dart            # weakness cards, type-coloured
      recommendations.dart        # problem list + Refresh, opens in browser
  ui/shell/home_shell.dart        # Dashboard tab → DashboardScreen (was placeholder)

mobile/test/
  analytics_models_test.dart      # JSON round-trip for every model
  analytics_repository_test.dart  # cached-first + offline-preserves-cache
  dashboard_screen_test.dart      # renders Overview → Insights; no-handle nudge
  support/analytics_fakes.dart    # fake API + sample builders
```

## Concepts Explained

### 1. Same cached-first contract as M2, generalised to 6 endpoints
The repository reads all cached sections → emits → fetches the six endpoints **in parallel** →
writes each back → re-emits. A failed fetch throws and the notifier keeps the cache (offline
guarantee), flipping a `fromCache` flag that raises the amber "showing saved analytics" note. First-
ever visit awaits the network (shimmer); everything after is instant from cache.

### 2. Cache storage reuses the drift `Settings` KV table
Rather than add per-section tables, each section is stored as a JSON blob under an `analytics.*`
key (`toJson` on the way in, `fromJson` on the way out). This is why every model round-trips — the
cache stores exactly what the server sent, and `readCache` reconstructs typed state. No schema
migration was needed.

### 3. Poll while syncing (mirrors the web)
`is_syncing` is true when the user's handle sync is running or has never completed. The notifier
starts a 5s `Timer` while syncing and cancels it the moment a fetch returns `is_syncing: false`, so
a freshly-linked account fills in without a manual refresh. The timer is cancelled on dispose.

### 4. Heatmap on a CustomPainter (no chart dep)
53 week-columns × 7 weekday-rows ending today, coloured by total submission count in five buckets
(0 / 1–2 / 3–5 / 6–9 / 10+) — the web thresholds. Grid dates are computed from the local "today"
back through the weeks; a tap hit-tests the cell and shows that day's solved count in the header.
Only the rating chart needed a package (`fl_chart`).

### 5. No handle yet → honest nudge, not a broken dashboard
`has_verified_handle == false` short-circuits to a "link your Codeforces handle on the web" nudge.
Handle verification is an M5 deliverable; the dashboard doesn't pretend to have data it can't get.

### 6. Sign-out must wipe private cache (privacy on a shared device)
Analytics is the first **private, per-user** data cached locally — unlike the public contests
cache. Left alone, account-switching on one device would show User A's dashboard (and keep firing
A's reminders) for User B. So `signOut` now clears the user-scoped drift rows (`analytics.*`,
starred contests, platform rules, scheduled reminders, reminder settings), cancels all OS-scheduled
notifications, and invalidates the in-memory providers. The public contests cache is intentionally
kept. A test pins that private data is wiped while the contest cache survives.

## Verification

```bash
cd mobile
export PATH="$HOME/dev/flutter/bin:$PATH"
flutter analyze                        # No issues found
flutter test                           # 40 passed (was 31)
flutter build apk --release --dart-define=API_BASE_URL=https://prognos-api.onrender.com  # ✓ 60 MB
```

- **Widget-tested UI (no device/auth needed):** `dashboard_screen_test.dart` pumps the real
  `DashboardScreen` with populated data and asserts the stat strip, heatmap, and `fl_chart` render,
  then toggles to Insights and asserts the tag list + Focus Areas; a second case asserts the
  no-handle nudge. This exercises the whole M4 render path in the test env.
- **Data layer:** model JSON round-trip for every type; repository caches all sections and preserves
  the cache when the network is down.
- **Release build** validates `fl_chart` survives R8 (the M3 `workmanager`/Room keep rules already
  in place).
- **Device-gated:** seeing *your own* live dashboard needs a verified handle + the Android OAuth
  client (M1 manual step) — same gate as every authed screen.

## Key Takeaways
- The M2 cached-first pattern generalises cleanly to a multi-endpoint screen — parallel fetch, blob
  cache, never clear on failure.
- Round-trippable models let a generic KV table be the offline cache with zero schema churn.
- A `CustomPainter` heatmap keeps the dependency budget down; reserve chart packages for what truly
  needs them.

## Next
**M5 — Classrooms + handle verification:** leaderboard / cohort / members / invites, the
`prognos://join/{token}` deep link, and the CF handle-verify flow (which unlocks this dashboard with
live data on-device).
