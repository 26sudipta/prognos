# PROGNOS Mobile — Implementation Plan (Android + iOS, Flutter)
**Status:** Approved plan — not yet implemented. Build one vertical slice at a time (CLAUDE.md §2).
**Supersedes:** `mobile_android_implementation_plan.md` (Kotlin/Android-only). The user now wants
**both Android and iOS**; that broke the Android-native premise. Its backend-auth design, reminder
architecture, and build order carry over — re-based on Flutter.

---

## 1. Context & market position (research, July 2026)

- **The field is open.** Category leader Codeforces WatchR (4.7★, 10K+) **shut down Nov 2023**;
  Snow stalled 2023; CodeChef's app is single-platform + notification spam. **No app combines:**
  reliable multi-platform contest alarms + streaks/heatmaps + classroom leaderboards. That trio is
  exactly PROGNOS. Wedge: **"the reminder that actually fires, plus your streak."**
- **#1 review-killer in this niche:** reminders silently dying (OEM battery killers — Huawei/
  Xiaomi/OnePlus/Samsung; Android 14+ denies exact alarms by default). v1 therefore ships a
  first-run **"Make reminders reliable"** screen — permission grant + per-OEM battery-whitelist
  guidance (dontkillmyapp patterns). This is a feature, not polish.
- **Stack: Flutter (user decision, research-backed).** One codebase → both stores.
  `flutter_local_notifications` v22 is actively maintained with explicit Android-14 exact-alarm,
  iOS 64-limit, and timezone support; RN's best equivalent (Notifee) was **archived Apr 2026** —
  disqualifying for a notifications-first app. Matches the original spec (requirement.md Module F).

**Positioning:** the app is a peer product to the web, not a companion. Feature parity with web
(read-only analytics per the "dumb frontend" rule) **plus** the mobile-only headline: **local
contest reminders/alarms** — scheduled on-device, works offline, zero server push (Module F.2).

---

## 2. Finalized requirements

### v1 (ship both stores)
| # | Requirement | Source |
|---|---|---|
| R1 | **Local contest reminders** — per-contest bell + **auto-remind rules** per platform ("all Codeforces", "all AtCoder"); default lead times **1 h + 15 min**, user-editable (10m/30m/1h/6h/1d) | Module F + market research (rules = retention; fixed timings are the top competitor complaint) |
| R2 | Reminders fire **offline, screen off, after reboot, through Doze**; correct across timezone/DST changes | Module F.2, §7.5 |
| R3 | "Make reminders reliable" first-run flow (exact-alarm permission, notifications permission, OEM battery guidance) | research §2 |
| R4 | Feature parity: Dashboard (stat strip, heatmap, rating chart), Insights (tags, focus areas, recommendations), Contests (list/calendar/detail), Classrooms (list/leaderboard/cohort/members/invites/join), Handle verify, Settings | user: "no difference from the web" |
| R5 | **Cold start < 2 s to interactive content** (target ~1.5 s); cached-first: every previously-seen screen renders instantly from local store, refreshes in background — fully useful offline | user: load-time focus |
| R6 | **Design consistency with web:** dark-first, `#09090C` base, indigo accent, CF rating color ladder, platform colors, shimmer skeletons, `undefined|null|T` loading pattern | user: consistent design; `frontend/AGENTS.md` tokens |
| R7 | Android **home-screen widget**: next-contest countdown + current streak | research §5 (the Strava move) |
| R8 | Deep links: `prognos://join/{token}` (classroom), contest detail from notification tap | carried from Android plan |

### v1.1 (explicitly deferred)
Share cards (streak/rating → image → share sheet) · iOS widget · FCM online-backup channel for
reminders (local stays the offline guarantee; v1 is zero-server-push per spec) · watch: never.

---

## 3. Tech stack

| Concern | Choice | Why |
|---|---|---|
| Framework | **Flutter** (Dart, AOT, Impeller) | one codebase both stores; strongest notif plugin story 2026 |
| Notifications | **`flutter_local_notifications` v22 + `timezone`** (`zonedSchedule`) | exact alarms (alarm-clock class) on Android; iOS local notifs; TZ/DST-safe |
| Background refresh | **`workmanager`** (Android WorkManager / iOS BGAppRefreshTask) | refresh contest cache + reconcile alarms; never fires reminders itself |
| Local store | **`drift`** (SQLite) for contests/dashboard cache; `shared_preferences`-backed prefs | offline-first, cached-first rendering |
| Secure tokens | **`flutter_secure_storage`** (Keystore / Keychain) | refresh token at rest |
| HTTP | `dio` + interceptor auto-refresh on 401 (mirror web `_lib/api.ts` semantics) | one retry, deduplicated refresh |
| Charts | **`fl_chart`** (rating line) + **custom `CustomPainter` heatmap** | active ecosystem; heatmap stays tiny |
| State | `riverpod` | testable, matches repository pattern |
| Images | `cached_network_image` | avatars off the critical path |
| Widget | `home_widget` (Android v1) | R7 |
| OTA hotfix | **Shorebird** | patch Dart without store review |
| Auth | `google_sign_in` (native sheets) → backend ID-token exchange | see §5 |

Repo: **monorepo**, third peer module — `mobile/` (single Flutter project, `android/` + `ios/`
inside it). Same rationale as the Android plan: one API contract, one PROGRESS, one docs tree.
`.gitignore` gains Flutter entries (`mobile/build/`, `.dart_tool/`, keystores).

---

## 4. Reminder system — the star feature

Two distinct mechanisms (never merged):

1. **Cache/reconcile loop** — `workmanager` periodic task (6–12 h) + on every app open:
   fetch `GET /api/v1/contests` (30-day window, cached in drift) → compute desired set =
   (starred contests ∪ rule-matched contests) × lead times → diff against scheduled →
   schedule/cancel. **Idempotent**: stable notification IDs = `hash(contestId, leadTime)`.
2. **Firing** — OS-level, scheduled via `zonedSchedule` with
   `androidScheduleMode: alarmClock` (exact, Doze-proof, alarm-priority) on Android; plain
   scheduled local notification on iOS. Tap → deep link to contest detail (register URL one tap
   away).

**Android specifics:** request `POST_NOTIFICATIONS` (13+) at first reminder opt-in;
`SCHEDULE_EXACT_ALARM` grant screen via the reliability flow (denied by default on 14+; listen
for permission-state-changed and reschedule); `BOOT_COMPLETED` + `TIMEZONE_CHANGED`/`TIME_SET`
receivers → full reschedule (plugin supports this; verify in M3 tests).

**iOS specifics — the 64-pending cap:** schedule a **rolling window** — soonest-first, cap ~48
(headroom), reconcile the pending set on every foreground + BGAppRefreshTask. iOS background
execution is opportunistic → foreground reconcile is the guarantee; an unopened-for-weeks app
degrades gracefully (window was pre-scheduled).

**Reliability flow (R3):** first reminder opt-in walks: notifications permission → exact-alarm
grant (Android) → OEM-specific battery-whitelist step (detect manufacturer, show tailored
instructions, dismissible) → confirmation with a test notification.

---

## 5. Backend dependencies (small, additive — ship with M1)

Carried unchanged from the Android plan (`backend/app/api/v1/routes/auth.py`):
1. **`POST /api/v1/auth/google/mobile`** — body `{ id_token }` from native Google Sign-In.
   **Must verify signature + audience via `google-auth`** (the web callback skips verification
   safely because it's a server↔Google exchange; the mobile token arrives from the device —
   copying the no-verify pattern would be an auth bypass). Reuse `upsert_user`; return
   `{ access_token, refresh_token, expires_in }` in the body (no cookie).
2. **Body-based refresh** — extend `/auth/refresh` to accept the refresh token from the body /
   `Authorization` header when no cookie present; reuse `rotate_refresh_token` unchanged.
3. Everything else reused as-is: `/users/me`, `/handles*`, `/analytics/*`, `/contests*`,
   `/classrooms*` (already lightweight pre-computed JSON — Module F.3 satisfied).

---

## 6. Speed & design engineering (R5, R6)

- **Cached-first rendering:** first frame = read drift/prefs → render last-synced data →
  background refresh → diff-update with subtle "updated" tick. Spinners never appear on a screen
  seen before; shimmer skeletons only on true first visits (mirrors web pattern).
- **Deferred init:** before first frame only secure-storage read + local store open. Timezone DB
  load, sync, widget update, Shorebird check — all post-first-frame.
- **Measured, not aspirational:** release-mode (AOT) cold-start profiled per slice on a mid-tier
  Android device; budget ~1.5 s. Tree-shaken icons, subset fonts (Inter + JetBrains Mono to match
  web), no network on the critical path.
- **Design tokens ported once (M0):** a Dart `theme/` mirroring `frontend/app/globals.css` —
  bg `#09090C`, surface/border/text scales, indigo accent, success/warning/danger, CF rating
  ladder, platform colors. Material 3 dark-first; light theme deferred.

---

## 7. Build order (vertical slices — one at a time, mini-design before each)

| Slice | Delivers | Verify (headline) |
|---|---|---|
| **M0** | Flutter project in `mobile/`, theme/design system, riverpod+dio+drift wiring, CI build both platforms, cold-start baseline | `flutter build apk --release` + `flutter build ios --no-codesign` clean; baseline number recorded |
| **M1** | **Auth** — backend mobile endpoints (verified ID token!) + native Google Sign-In + secure token store + auto-refresh + session restore | tampered/expired ID token rejected server-side; kill+reopen restores silently; 401 → one refresh+retry |
| **M2** | **Contests + offline cache** — list/calendar/detail from drift, workmanager refresh, pull-to-refresh | airplane mode → full contest list renders; cache refreshes on schedule |
| **M3** | ⭐ **Reminders** — bell + platform rules, lead-time settings, exact alarms, iOS rolling window, reliability flow, boot/TZ reschedule, deep links | alarm fires screen-off/Doze at `start − lead`; survives reboot; un-star cancels; 65th iOS notification handled; DST shift correct |
| **M4** | **Dashboard + Insights** — stat strip, Canvas heatmap, fl_chart rating, tags/weaknesses/recs; cached-first | data matches web for same account; instant render from cache offline |
| **M5** | **Classrooms + handle verify** — leaderboard/cohort/members/invites, `prognos://join/{token}`, CF verify flow | join via deep link end-to-end; leaderboard matches web |
| **M6** | **Widget + polish + release** — Android widget (R7), perf hardening pass, accessibility, store listings, Shorebird, signed releases | cold start ≤ budget on mid-tier device; widget updates with cache; both stores submitted |

Each slice: mini-design approved first; `docs/phase_M_X.md` written after it passes (CLAUDE.md §5.2).

---

## 8. Open decisions (confirm during the relevant slice)
- Rule granularity v1: per-platform only, or platform+division filters (e.g. "Div 2+") — M3.
- Notification tap target: in-app contest detail (recommended) vs direct registration URL — M3.
- fl_chart vs tiny custom painter for the rating chart if size budget tightens — M4.
- Widget refresh cadence vs battery (WorkManager-driven, 6 h default) — M6.
