# PROGNOS Mobile (Flutter — Android + iOS)

Cross-platform app for PROGNOS. Headline feature: **reliable local contest
reminders** (offline, exact alarms). Plan: `docs/mobile_implementation_plan.md`.

## Prerequisites (your machine)

- **Flutter SDK 3.44+** — installed at `/home/sudipta/dev/flutter`. Add to PATH:
  ```bash
  export PATH="$HOME/dev/flutter/bin:$PATH"   # add to ~/.zshrc to persist
  ```
- **To run on Android:** Android Studio + Android SDK (includes an emulator).
  Then `flutter doctor --android-licenses`.
- **To run on iOS:** a Mac with Xcode (not possible on Linux).

Check your setup: `flutter doctor`

## Run

```bash
cd mobile
flutter pub get

# Against the LIVE backend:
flutter run --dart-define=API_BASE_URL=https://prognos-api.onrender.com

# Against a LOCAL backend (Android emulator reaches the host at 10.0.2.2):
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Default `API_BASE_URL` (no flag) is `http://10.0.2.2:8000`.

## Verify (no device needed)

```bash
flutter analyze     # static analysis — must be clean
flutter test        # unit + widget tests
```

## Project layout

```
lib/
  main.dart              # entry: ProviderScope + minimal first frame
  app.dart               # MaterialApp (dark-first)
  theme/                 # design system — mirrors frontend/app/globals.css
    app_colors.dart      #   exact web colour tokens
    app_theme.dart       #   Material 3 dark theme, Inter / JetBrains Mono
    cf_rating.dart       #   Codeforces rating colour ladder + rank labels
  core/
    config/app_config.dart    # API base URL (--dart-define), timeouts
    network/dio_client.dart   # Dio provider (auth interceptor added in M1)
    storage/secure_store.dart # encrypted token store (Keystore/Keychain)
  ui/
    shell/home_shell.dart     # 3-tab bottom nav (Dashboard/Contests/Leaderboard)
    widgets/skeleton.dart     # shimmer loader (mirrors web .skeleton)
```

## Build status

**M0 (foundation) — done.** Project scaffold, design system, core wiring, 3-tab
shell, tests green. Real screens land per slice (M1 auth → M2 contests → M3
reminders → M4 dashboard → M5 classrooms → M6 widget/release).
