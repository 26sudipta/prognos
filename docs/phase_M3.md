# Phase M3 — Contest Reminders ⭐

**Status:** Built & statically verified — 2026-07-03. The headline mobile feature: on-device
alarms that fire before a contest starts, offline and screen-off. Firing/permission/boot behaviour
is device-only (documented below); the scheduling logic is unit-tested.

## What Was Built

Star a contest (or enable a whole platform) → the app schedules exact local alarms at
`start − lead` for your chosen lead times → a tap deep-links into the contest detail. A reconcile
engine keeps the OS's scheduled set in sync with your intent, idempotently.

```
mobile/lib/
  core/db/app_database.dart            # + StarredContests, PlatformRules, ScheduledReminders,
                                       #   Settings tables (schemaVersion 2 + migration)
  core/reminders/
    reminder_ids.dart                  # deterministic FNV-1a → 31-bit notification id
    reminder_reconciler.dart           # PURE: desired-set, iOS cap, diff vs OS pending
    reminder_scheduler.dart            # flutter_local_notifications + timezone + tap plumbing
    reminders_repository.dart          # stars/rules/leads/ledger + reconcile()
    reminders_providers.dart           # riverpod: scheduler, repo, controller, isStarred(family)
  ui/reminders/
    reminder_bell.dart                 # per-contest toggle (runs onboarding on first opt-in)
    reliability_flow.dart              # notif → exact-alarm → OEM battery → test (bottom sheet)
    reminders_screen.dart              # lead times, platform rules, delivery re-check, upcoming
  ui/shell/home_shell.dart             # scheduler init, reconcile on foreground/cache-update, deep links
  ui/contests/widgets/contest_card.dart, contest_detail_sheet.dart   # + ReminderBell

mobile/android/app/
  src/main/AndroidManifest.xml         # POST_NOTIFICATIONS, SCHEDULE_EXACT_ALARM, RECEIVE_BOOT_COMPLETED,
                                       #   VIBRATE, battery-opt; FLN boot/scheduled receivers
  build.gradle.kts                     # core-library desugaring (FLN 22 needs java.time)

mobile/test/
  reminder_ids_test.dart               # determinism + 31-bit range
  reminder_reconciler_test.dart        # desired-set, lead-passed, platform rule, iOS cap, diff
  reminders_repository_test.dart       # reconcile schedules/cancels against a fake OS
  support/reminder_fakes.dart          # in-memory scheduler
```

## Concepts Explained

### 1. Two mechanisms, never merged: reconcile vs fire
Scheduling is a **reconcile loop**; firing is the **OS**. The loop computes a *desired* set from
(starred ∪ platform-rule-matched) contests × lead times, each keyed by a **deterministic ID**, then
diffs it against what's actually scheduled and applies only the delta. Because IDs are stable,
re-running is idempotent — the same star never double-schedules. The OS then fires independently via
`zonedSchedule`, so alarms work with the app closed.

### 2. Reconcile against the OS, not our own ledger
`pendingNotificationRequests()` is the source of truth for "what's scheduled" — our drift ledger
*will* drift (reboot, iOS eviction past the 64-cap, user-cleared notifications). So `reconcile`
computes `desired`, reads OS `pending`, and schedules `desired − pending` / cancels
`pending − desired`. The `scheduled_reminders` table is kept only as **intent** (it drives the
settings "upcoming" list), never as the diff source.

### 3. Deterministic, 31-bit-safe IDs (two real traps)
`reminderNotifId` is FNV-1a over `"contestId:leadMin"`, masked to 31 bits. Two reasons this isn't
`Object.hash`: (a) Android notification IDs are Java `int` — anything above 2³¹−1 misbehaves, so we
mask; (b) the ID must be **identical across isolates and app restarts**, and Dart's built-in hashes
aren't guaranteed stable, so a fixed algorithm is required. Both are pinned by tests.

### 4. Timezone correctness — the silent DST bug
`timezone` ships the IANA database but not "which zone is this device in." Without
`tz.setLocalLocation`, `tz.local` defaults to **UTC** and every alarm fires off by the device's
offset. Init does `tz.initializeTimeZones()` → `setLocalLocation(getLocation(FlutterTimezone…))`
before any scheduling, and fire times are `TZDateTime` (DST-correct).

### 5. Doze/reboot survival is manifest + schedule-mode
Alarms use `AndroidScheduleMode.alarmClock` — the most Doze-exempt mode (not rate-limited in deep
Doze), so they fire screen-off. `RECEIVE_BOOT_COMPLETED` + FLN's boot receiver reschedule every
pending alarm after a reboot or app update. On 14+, `SCHEDULE_EXACT_ALARM` is not auto-granted, so
the reliability flow requests it at opt-in.

### 6. The reliability flow (why alarms silently die)
First opt-in walks: notifications permission → exact-alarm grant → **OEM battery-optimisation
whitelist** (the real killer on Xiaomi/Oppo/Vivo/…, detected via `device_info_plus` with tailored
instructions) → a test notification so the user sees it work. Re-runnable from the Reminders screen.

### 7. Deep links: cold launch ≠ warm tap
A tap while the app runs arrives on the `taps` stream; a tap that **cold-launches** the app is
delivered separately via `getNotificationAppLaunchDetails()`. Both are wired, and navigation is
deferred until auth + the contest cache are ready (a pending-link is flushed when contests load), so
the detail sheet can actually be shown.

### 8. Single-isolate reconcile (deliberate)
Reconcile runs only in the **main isolate** — on app open, on foreground (`resumed`), and whenever
the contest cache updates. The M2 background workmanager task refreshes the *cache* but does not
reconcile, avoiding the complexity (and bug surface) of initializing the notification plugin inside
the headless isolate. New contests that appear while the app is closed are picked up on the next
open/foreground — which is also exactly the iOS reconcile guarantee.

## Verification

```bash
cd mobile
export PATH="$HOME/dev/flutter/bin:$PATH"
dart run build_runner build            # regenerate app_database.g.dart after schema change
flutter analyze                        # No issues found
flutter test                           # 31 passed (was 19)
flutter build apk --debug   --dart-define=API_BASE_URL=https://prognos-api.onrender.com
flutter build apk --release --dart-define=API_BASE_URL=https://prognos-api.onrender.com  # ✓ 59 MB
```

The **release** build is the one that matters here, and it caught a real ship-blocker: R8 is
active in release and stripped a reflectively-instantiated constructor, crashing the app **at
process start, before Flutter even loads** (`Unable to get provider
androidx.startup.InitializationProvider … NoSuchMethodException:
androidx.work.impl.WorkDatabase_Impl.<init>`). The culprit was the `workmanager` plugin's
`androidx.work`/Room database, not `flutter_local_notifications`. Fix: keep rules for
`androidx.work` + `androidx.room` + Room DB constructors (plus the FLN/Gson keeps) in
`android/app/proguard-rules.pro`. Verified by installing the release APK on an emulator and
confirming it launches to the login screen — a debug build would never have surfaced this.

**Unit-tested (the logic core):** ID determinism + 31-bit range; desired-set (lead-already-passed
dropped, platform rule, started-contest ignored); iOS cap keeps the soonest N; diff → correct
schedule/cancel sets; repository reconcile schedules on star and cancels on un-star against a fake
OS.

**Device-only (state honestly, not faked):** actual alarm delivery screen-off/Doze, survival across
reboot, permission grant screens, and the OEM battery step must be verified on a physical Android
device (and the iOS 64-cap on a device). The reconcile logic they depend on is what the tests pin.

## Key Takeaways
- Separate *reconcile* (idempotent, ID-keyed) from *firing* (OS); reconcile against the OS pending
  set, not your own table.
- Notification IDs must be deterministic across isolates/restarts **and** fit 31 bits.
- `setLocalLocation` is mandatory or every alarm is offset-wrong; `alarmClock` + boot receiver are
  what make "screen-off" and "survives reboot" true.
- On Android the battery-optimisation whitelist is the difference between reminders that work and
  reminders that silently never fire.

## Next
**M4 — Dashboard + Insights:** stat strip, Canvas activity heatmap, `fl_chart` rating chart, tags /
weaknesses / recommendations — cached-first from drift, matching the web for the same account.

## Updates

### Reliability flow simplified for non-technical users
The original opt-in sheet told users to hunt through OEM battery menus ("remove PROGNOS from
*sleeping apps*") and asked for the *exact-alarm* system grant — jargon a normal user can't act on.
Replaced with a two-state sheet (`reliability_flow.dart`):
1. **Enable** — two one-tap system dialogs (notifications + background activity), then it schedules
   an **honest test**: a real alarm ~15 s out through the *same* `zonedSchedule` + `alarmClock` path
   real reminders use (`ReminderScheduler.scheduleTest`). The old "test" called `_fln.show()` — an
   *immediate* notification that lights up green even on a phone that silently drops scheduled
   alarms, i.e. a false positive. The new test actually proves the bell will ring on this device.
2. **Verify** — "Did the test alert arrive? *Yes* / *Didn't get it* / *Test again*", with a
   Do-Not-Disturb tip (DND silences the channel — the first thing to check).

`USE_EXACT_ALARM` was added to the manifest so exact alarms are auto-granted on API 33+ (no prompt);
`SCHEDULE_EXACT_ALARM` stays for older APIs. See `docs/mobile_release_checklist.md` for the Play
Console "Exact alarm" declaration this requires.

### The reminder that never rang — resource shrinker stripped the notification icon
**Symptom (device):** the test alert never rang, and after it *should* have fired the app showed
"PROGNOS keeps stopping" — crash-looping on every launch.

**Root cause:** a release-only crash, invisible in debug. The small status-bar icon
`res/drawable/ic_stat_reminder.xml` is referenced **only by string name** from Dart
(`AndroidInitializationSettings('ic_stat_reminder')` and `AndroidNotificationDetails.icon`), never
from any XML/manifest. Release builds run the **resource shrinker**, which sees no static reference
and removes it — the shrinker report says it outright:

```
drawable:ic_stat_reminder:2131230879 is not reachable.
```

At fire time the notification then has no valid small icon and the native path throws, taking down
the whole process:

```
FATAL EXCEPTION: ScheduledNotificationReceiver
IllegalArgumentException: Invalid notification (no valid small icon):
    Notification(channel=contest_reminders ...)
```

Because flutter_local_notifications persists the scheduled alarm, it **re-fires on every launch**,
so the crash loops. One missing resource explained *both* "no bell" and "keeps stopping".

**Fix:** `android/app/src/main/res/raw/keep.xml` tells the shrinker to keep the icon —

```xml
<resources xmlns:tools="http://schemas.android.com/tools"
    tools:keep="@drawable/ic_stat_reminder" />
```

and the scheduler now passes `icon: 'ic_stat_reminder'` explicitly on every
`AndroidNotificationDetails` (self-documenting; the name is also centralised in a `_kSmallIcon`
const). Rebuilt release now reports `reachable from keep xml file`, and on the physical
Samsung SM-M105F the test alarm posts a live `StatusBarNotification` with
`icon=… drawable/ic_stat_reminder` and vibrates — no crash.

**Diagnosis note:** this is the *same lesson* as the earlier workmanager R8 crash above — anything
reachable only by reflection or by string-name is invisible to R8/the resource shrinker and must be
kept explicitly. Always verify notification and widget resources against a **release** APK
(`aapt2 dump resources app-release.apk | grep <name>` and the shrinker's `resources.txt` report),
never just debug. Also: build sideload/landing APKs **universal** (all ABIs) — this 32-bit device
(`armeabi-v7a`) can't run an `--target-platform android-arm64` build (`Could not find libflutter.so`).

**Verification (release APK, on device):**
```bash
flutter build apk --release --dart-define=API_BASE_URL=https://prognos-api.onrender.com
aapt2 dump resources build/app/outputs/flutter-apk/app-release.apk | grep ic_stat_reminder
#   → resource 0x7f08009f drawable/ic_stat_reminder        (present)
grep ic_stat_reminder build/app/outputs/mapping/release/resources.txt
#   → drawable:ic_stat_reminder:… reachable from keep xml file
# then: Reminders → Check reminder settings → Enable → wait ~15 s → alert rings, no crash.
```

### Real reminders never fired — Samsung deep-sleep wipes the alarms (+ two latent bugs)

**Symptom:** the 15-second test rings reliably (screen off, app closed), but real contest
reminders never fire at contest time — on the fixed build, for both starred and platform reminders.

**Root cause (confirmed on-device):** the reminders *are* scheduled correctly as Doze-exempt
`setAlarmClock` alarms with correct fire times (timezone/`toUtc()` is instant-preserving, so the
epoch is right regardless of `tz.local`). The problem is **Samsung One UI "Deep sleep / Sleeping
apps" force-stops the app when it's idle, and force-stopping an app cancels every AlarmManager alarm
it owns.** Proven with `adb`:

```
dumpsys alarm | grep -c walarm.*io.prognos.prognos   → 7   (armed)
adb shell am force-stop io.prognos.prognos            → (deep-sleep does exactly this)
dumpsys alarm | grep -c walarm.*io.prognos.prognos   → 0   (all wiped)
```

Nothing re-arms them until the app is next opened, so a contest that occurs while the app is
deep-slept gets no reminder. The 15 s test survives only because the app is active when it runs.
`REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` does **not** exclude an app from One UI deep-sleep.

**Fixes (this change):**

1. **Ring through Do Not Disturb** — the reminder channel now uses `AudioAttributesUsage.alarm`
   (DND permits alarms), so an alarm that fires during DND is audible instead of silently dropped.
   Channels are immutable once created, so the id is versioned `contest_reminders` →
   `contest_reminders_v2` and the old channel is deleted on `init`. Verified on-device: the posted
   notification's `effectiveNotificationChannel` shows `usage=USAGE_ALARM`.
2. **Reconcile no longer cancels out-of-window alarms** (latent bug). `reconcile` recomputes the
   desired set from the 30-day/200-item cache and used to cancel *every* pending alarm not in it —
   so any starred/enabled contest that aged out of the fetched window had its still-correct alarm
   wiped. `diffReminders` now takes a `managedIds` set (`managedReminderIds` = every id derivable
   from the *current* cache) and only cancels ids in it; an alarm whose contest has left the cache
   is left armed. Unit-tested: "leaves alarms armed for contests that aged out of the cache window."
3. **Deep-sleep guidance** — the reliability flow's "Didn't get it" tip now leads with the actual
   fix for Samsung: Battery → Background usage limits → remove PROGNOS from "Sleeping apps" /
   "Deep sleeping apps" and add it to **"Never sleeping apps"** (with the *why*: sleeping apps get
   force-stopped, which cancels alarms). Manufacturer-specific copy for Xiaomi/Oppo/Vivo too.

**Honest limitation:** on aggressive OEMs (Samsung especially), no purely on-device local-alarm app
can guarantee delivery unless the user excludes it from deep-sleep — a WorkManager re-arm doesn't
help because force-stop cancels its jobs too. The only zero-config guarantee is a **server FCM push**
at contest time (previously deferred in favor of on-device); revisit if whitelisting proves too much
to ask of users.
