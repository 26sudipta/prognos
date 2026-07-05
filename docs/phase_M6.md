# Phase M6 — Home-Screen Widget + Polish + Release

**Status:** Built & verified — 2026-07-04. The final mobile slice: an Android home-screen widget,
an accessibility/perf pass, and release plumbing (signing, store listing, Shorebird, OAuth) wired for
the user to finish with their own secrets/accounts.

## What Was Built

```
mobile/lib/core/widget/home_widget_service.dart   # buildWidgetPayload() + updateHomeWidget()
mobile/lib/core/background/refresh_worker.dart     # update widget after the bg cache refresh
mobile/lib/ui/shell/home_shell.dart                # update widget on cache/analytics change
mobile/android/app/src/main/
  kotlin/io/prognos/prognos/ContestWidgetProvider.kt  # RemoteViews provider (reads home_widget prefs)
  res/layout/contest_widget.xml + drawable/widget_bg.xml + xml/contest_widget_info.xml
  AndroidManifest.xml                              # <receiver> for the widget
mobile/android/app/build.gradle.kts                # conditional release signingConfig
mobile/ui/classrooms/classroom_detail_screen.dart  # tooltips on icon-only buttons (a11y)
docs/store_listing.md · docs/mobile_release_checklist.md
mobile/test/home_widget_test.dart                  # payload mapping
```

## Concepts Explained

### 1. The widget renders pre-computed values — it never reads drift
A home-screen widget is native `RemoteViews`; it can only display what `home_widget` wrote to its
SharedPreferences. So the flow is **compute in Dart, render dumb**: `buildWidgetPayload(db)` reads
the contests cache (reusing `nextContest`) and the cached dashboard streak, returns a flat
`{next_title, next_subtitle, streak}` map; `updateHomeWidget` saves those keys and calls
`updateWidget`; the Kotlin `ContestWidgetProvider` reads them into the layout. This matches the
app's "frontends are dumb" rule. The payload builder is the unit-tested core.

### 2. A widget can't tick — static relative string, recomputed on update
Android refreshes widgets at most ~every 30 min, and our background cycle is 6 h, so a per-second
countdown is impossible without the app running. The widget shows a **static** relative string
(`in 3h 12m` / `LIVE` / `in 2d`), recomputed on every update (app open, cache refresh, the 6 h
workmanager cycle) — never on a `Timer`. (A live-ticking upgrade would use an Android `Chronometer`
in RemoteViews; deferred — it's ugly for far-future contests.)

### 3. Updated from both isolates
`updateHomeWidget` is called from the **main isolate** (on cache/analytics change, via `ref.listen`)
and the **workmanager headless isolate** (after the background cache refresh) — the isolate already
does `DartPluginRegistrant.ensureInitialized()`, so the `home_widget` channel works there just like
the contest refresh. Graceful when no widget is placed or the streak cache is absent (shows `—`).

### 4. Signing must not break a keyless build
`build.gradle.kts` loads `key.properties` **only if it exists**; the release build signs with the
real keystore when present and falls back to debug otherwise. This keeps `flutter build apk
--release` working in CI / locally without the (gitignored) secret, while a real release just needs
the file. Verified by building release right after wiring it — still succeeds with debug signing.

### 5. R8 and the widget provider
The provider is referenced from `AndroidManifest` (`<receiver>`), and manifest-referenced classes are
R8 keep-roots — so, unlike the M3 workmanager/Room case, it isn't stripped, and `home_widget` ships
consumer rules. Confirmed the way M3/M5 were: the release APK installs and launches on the emulator.

## Verification

```bash
cd mobile
export PATH="$HOME/dev/flutter/bin:$PATH"
flutter analyze                        # No issues found
flutter test                           # 55 passed (was 52)
flutter build apk --release --dart-define=API_BASE_URL=https://prognos-api.onrender.com
```

- **Payload mapping** unit-tested: empty cache → placeholder + `—`; next contest → title/subtitle
  with platform + relative time; live contest → `LIVE`.
- **Signing** keyless fallback verified by the release build succeeding without `key.properties`.
- **Emulator:** release APK installs + launches; the widget provider registers without a manifest
  error and renders "next contest + streak" when added to the home screen.

## What's user-gated (documented, can't run here)
Real keystore + `key.properties`, Play/App Store submission, Shorebird account/init, physical-device
cold-start + reminder-firing + widget checks, and the outstanding **Android OAuth client** (package
`io.prognos.prognos` + debug **and** release SHA-1). All in `docs/mobile_release_checklist.md`.

## Brand Consistency + Audit Pass (post-review)

A design-consistency + logic audit was run after the core M6 work:

- **Logo mismatch fixed.** The app used a lightning **bolt**; the web favicon
  (`frontend/app/icon.tsx`) is an indigo (`#6366F1`) rounded square + white lucide **trending-up**
  arrow. Generated the exact mark (`tool/gen_logo.py` → `assets/icon/`), wired **launcher icons**
  (`flutter_launcher_icons`, adaptive incl. Android 13 monochrome) and a **dark launch splash**
  (`flutter_native_splash`, bg `#070B14` + logo — no white flash, matches the web login). A shared
  `AppLogo` widget is now the single source of truth; the auth-gate loading screen uses an
  `AnimatedAppLogo` (breathing pulse) instead of a static bolt.
- **App name casing** unified to `PROGNOS` (Android label + iOS `CFBundleDisplayName`) to match the
  web wordmark.
- **Sign-out privacy completeness (all four per-user roots).** The audit found
  `handleControllerProvider` was per-user, non-autoDispose, and *not* invalidated on sign-out —
  User B opening the verify screen would have seen User A's handle state. `signOut` now invalidates
  **analytics + reminders + classroomsList + handleController** (the complete set; contests is public
  and intentionally kept). Known minor: the `leaderboard/members/cohort/invites` *family* providers
  aren't invalidated — but that's shared classroom data (visible to all members by the transparency
  model) and refetches on open, so it's left as-is.

## Key Takeaways
- Widgets render pre-computed flat values and can't tick — compute in Dart, push on events, use a
  static relative string.
- Update the widget from every isolate that touches the cache.
- Gate the signing config on the secret file's existence so keyless builds never break.

## Next
Mobile milestones M0–M6 are complete. Remaining before public launch is entirely user-side: create
the OAuth clients, a signing keystore, store listings + screenshots, and submit — per
`docs/mobile_release_checklist.md`.
