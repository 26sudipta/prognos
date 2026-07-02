# Phase M0 — Mobile Foundation (Flutter)

**Status:** DONE — 2026-07-02. First slice of the mobile app (`docs/mobile_implementation_plan.md`).

## What Was Built

Flutter 3.44.4 project at repo root `mobile/` (Android + iOS platforms), plus the
design-system + core-wiring foundation every later slice builds on.

```
mobile/
├── pubspec.yaml                     # deps: flutter_riverpod, dio, google_fonts, intl,
│                                    #       flutter_secure_storage
├── README.md                        # setup + run + verify instructions (for the user)
├── .gitignore                       # + keystore/secret ignores
├── android/ ios/                    # native scaffolds (generated)
├── test/widget_test.dart            # 3 tests: shell boot, tab switch, CF ladder
└── lib/
    ├── main.dart                    # ProviderScope + minimal first frame
    ├── app.dart                     # MaterialApp, dark-first
    ├── theme/
    │   ├── app_colors.dart          # exact web colour tokens
    │   ├── app_theme.dart           # Material 3 dark theme + typography
    │   └── cf_rating.dart           # CF rating colour ladder + rank labels
    ├── core/
    │   ├── config/app_config.dart   # API base URL via --dart-define
    │   ├── network/dio_client.dart  # Dio provider
    │   └── storage/secure_store.dart# encrypted token store provider
    └── ui/
        ├── shell/home_shell.dart    # 3-tab bottom nav
        ├── shell/placeholder_screen.dart
        └── widgets/skeleton.dart    # shimmer loader
```

## Concepts Explained

### 1. Why the SDK is installed user-local, not system-wide
Flutter lives at `/home/sudipta/dev/flutter` (outside the repo, added to PATH), not via
`snap`/`apt`. No sudo, no system pollution, trivially removable, and pinned to 3.44.4 so builds
are reproducible. The Dart SDK ships inside Flutter — nothing else to install.

### 2. Design system mirrors the web, byte-for-byte
`app_colors.dart` and `cf_rating.dart` are **transcriptions of the live web tokens**
(`frontend/app/globals.css` and the stat-strip rating ladder), not re-picked shades — base
`#070B14`, indigo `#6366F1`, the CF ladder `#F44336`→`#9E9E9E`. This is what makes the app read
as the same product as the web. If the web tokens change, these two files change with them.
Body text uses Inter and numbers/ratings use JetBrains Mono via `google_fonts`, matching the web
fonts. (M6 swaps runtime `google_fonts` for bundled, subsetted fonts to remove the network fetch
from the cold-start path.)

### 3. Riverpod providers wire the seams before the features exist
`dioProvider` (HTTP transport) and `secureStoreProvider` (encrypted token store) are in place now
so M1 (auth) only adds the interceptor and the sign-in flow — no re-plumbing. The API base URL is
a compile-time `--dart-define` (`AppConfig.apiBaseUrl`), defaulting to the Android-emulator host
loopback `10.0.2.2:8000`, so the same binary points at local or live by build flag.

### 4. Cold-start discipline starts at line one
`main()` does only `ensureInitialized()` + `runApp`. No sync, no timezone DB, no analytics on the
first frame — those are deferred to the slices that introduce them (plan §6). The habit is
cheaper to keep than to retrofit.

### 5. The shell proves the foundation renders
A 3-tab `NavigationBar` (Dashboard / Contests / Leaderboard) over an `IndexedStack` (preserves tab
state). Each tab is a `PlaceholderScreen` rendered with the **real** theme + the shimmer
`Skeleton` — so M0 visibly demonstrates the whole design system end-to-end, and each later slice
just swaps a placeholder for its real screen.

## Verification

```bash
export PATH="$HOME/dev/flutter/bin:$PATH"
cd mobile
flutter analyze     # → No issues found!
flutter test        # → All tests passed! (3 tests)
```

- `flutter analyze` — clean (0 issues).
- `flutter test` — 3 passing: app boots to the shell, tab switch shows the Contests screen, and
  the CF rating ladder matches the web thresholds exactly.
- Running on a device/emulator or producing an APK requires the Android SDK (user's machine) — out
  of scope for M0, which is verified statically. See `mobile/README.md`.

## Key Takeaways

- The mobile app is a **peer to the web**, and consistency is enforced by transcribing the web's
  colour/rating tokens rather than re-designing them.
- Core seams (HTTP, secure storage, config, theme, shell) exist **before** features, so slices add
  screens without touching plumbing.
- Cold-start budget is protected from the first commit; `google_fonts` runtime fetch is the one
  known cold-start cost, explicitly deferred to M6.

## Next
**M1 — Auth.** Backend adds `POST /api/v1/auth/google/mobile` (**verified** Google ID-token
exchange) + body-based refresh; the app adds native Google Sign-In, the Dio auth interceptor
(Bearer + one-shot refresh-on-401), and silent session restore from the secure store. M1 will
pause for the user to create the Google OAuth client IDs (Android/iOS).
