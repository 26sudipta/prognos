import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import '../contests/contest_format.dart';
import 'reminder_reconciler.dart';

const _kChannelId = 'contest_reminders';
const _kChannelName = 'Contest Reminders';

/// Monochrome status-bar icon. Referenced by name so the release resource
/// shrinker can't see it statically — it is force-kept via `res/raw/keep.xml`.
/// A missing small icon makes the notification receiver throw at fire time and
/// crash-loops the app, so this must always resolve.
const _kSmallIcon = 'ic_stat_reminder';

/// Broadcasts the `contestId` payload of a tapped reminder while the app is
/// running. Top-level so the plugin's static callback can reach it.
final StreamController<String> _tapController =
    StreamController<String>.broadcast();

@pragma('vm:entry-point')
void _onNotificationTap(NotificationResponse response) {
  final payload = response.payload;
  if (payload != null && payload.isNotEmpty) _tapController.add(payload);
}

/// Thin wrapper over `flutter_local_notifications` + `timezone`. Owns init,
/// scheduling, cancellation, and permission requests. All timezone-correctness
/// and OS-cap logic lives here; the *desired set* is computed purely in
/// [reminder_reconciler].
class ReminderScheduler {
  final FlutterLocalNotificationsPlugin _fln =
      FlutterLocalNotificationsPlugin();
  bool _ready = false;

  /// Emits the `contestId` of a reminder tapped while the app is running.
  Stream<String> get taps => _tapController.stream;

  /// One-time init: timezone database + **device local zone** (without
  /// `setLocalLocation`, `tz.local` is UTC and every alarm fires off by the
  /// device's offset), then the plugin with tap callbacks.
  Future<void> init() async {
    if (_ready) return;
    tzdata.initializeTimeZones();
    try {
      final info = await FlutterTimezone.getLocalTimezone();
      tz.setLocalLocation(tz.getLocation(info.identifier));
    } catch (e) {
      debugPrint('Timezone init failed ($e) — reminders may be off by offset');
    }

    // Monochrome status-bar icon — a full-color launcher icon renders as a
    // white square when Android tints the small icon.
    const android = AndroidInitializationSettings(_kSmallIcon);
    const ios = DarwinInitializationSettings(
      requestAlertPermission: false, // asked explicitly in the reliability flow
      requestBadgePermission: false,
      requestSoundPermission: false,
    );
    await _fln.initialize(
      settings: const InitializationSettings(android: android, iOS: ios),
      onDidReceiveNotificationResponse: _onNotificationTap,
      onDidReceiveBackgroundNotificationResponse: _onNotificationTap,
    );
    _ready = true;
  }

  /// The `contestId` payload if the app was **cold-launched** by tapping a
  /// reminder (a different API from the running-app stream). Consume once,
  /// after auth + cache are ready.
  Future<String?> initialLaunchContestId() async {
    final details = await _fln.getNotificationAppLaunchDetails();
    if (details?.didNotificationLaunchApp == true) {
      return details!.notificationResponse?.payload;
    }
    return null;
  }

  /// Schedule one reminder at its exact fire time. Uses
  /// [AndroidScheduleMode.alarmClock] — the most Doze-exempt mode (not
  /// rate-limited in deep Doze), so alarms fire screen-off.
  Future<void> schedule(DesiredReminder r) async {
    final when = tz.TZDateTime.from(r.fireAt.toUtc(), tz.local);
    final name = r.contest.name;
    final lead = r.leadMinutes >= 60
        ? '${r.leadMinutes ~/ 60}h'
        : '${r.leadMinutes}m';
    await _fln.zonedSchedule(
      id: r.notifId,
      title: '$name starts in $lead',
      body: '${platformDisplayName(r.contest.platform)} · tap for details',
      scheduledDate: when,
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          _kChannelId,
          _kChannelName,
          channelDescription: 'Alerts before your starred contests begin',
          importance: Importance.max,
          priority: Priority.high,
          category: AndroidNotificationCategory.reminder,
          icon: _kSmallIcon,
        ),
        iOS: DarwinNotificationDetails(),
      ),
      androidScheduleMode: AndroidScheduleMode.alarmClock,
      payload: r.contest.id,
    );
  }

  Future<void> cancel(int notifId) => _fln.cancel(id: notifId);

  /// Cancel every scheduled reminder — used on sign-out so the previous user's
  /// alarms never fire for a different account on this device.
  Future<void> cancelAll() async {
    try {
      await _fln.cancelAll();
    } catch (_) {
      // Plugin not initialised (never opened the app authed) — nothing to cancel.
    }
  }

  /// IDs the OS currently has scheduled. This app only schedules reminders, so
  /// every pending request is ours — the authoritative reconcile baseline.
  Future<Set<int>> pendingIds() async {
    final pending = await _fln.pendingNotificationRequests();
    return pending.map((p) => p.id).toSet();
  }

  static const int _kTestId = 424242;

  /// Schedule a test alert ~15s out through the **real** alarm path
  /// (`zonedSchedule` + `alarmClock`) — the same path real reminders use. An
  /// *immediate* `show()` would light up green even on a phone that silently
  /// drops scheduled alarms; this is the honest test that actually proves the
  /// bell will ring on this device.
  Future<void> scheduleTest() async {
    final when = tz.TZDateTime.now(tz.local).add(const Duration(seconds: 15));
    await _fln.zonedSchedule(
      id: _kTestId,
      title: 'Test reminder 🔔',
      body: 'Your contest reminders will ring like this.',
      scheduledDate: when,
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          _kChannelId,
          _kChannelName,
          importance: Importance.max,
          priority: Priority.high,
          category: AndroidNotificationCategory.reminder,
          icon: _kSmallIcon,
        ),
        iOS: DarwinNotificationDetails(),
      ),
      androidScheduleMode: AndroidScheduleMode.alarmClock,
    );
  }

  // ─── Permissions ──────────────────────────────────────────────────────────

  /// Request the notifications permission (Android 13+ / iOS). Returns whether
  /// it is granted.
  Future<bool> requestNotificationsPermission() async {
    final android = _fln.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (android != null) {
      return await android.requestNotificationsPermission() ?? false;
    }
    final ios = _fln.resolvePlatformSpecificImplementation<
        IOSFlutterLocalNotificationsPlugin>();
    if (ios != null) {
      return await ios.requestPermissions(alert: true, badge: true, sound: true) ??
          false;
    }
    return true;
  }

  /// Whether exact alarms can be scheduled. With `USE_EXACT_ALARM` declared this
  /// is true on 13+ without any prompt, so the flow never opens a settings
  /// screen for it. True on iOS.
  Future<bool> canScheduleExactAlarms() async {
    final android = _fln.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (android == null) return true;
    return await android.canScheduleExactNotifications() ?? true;
  }
}
