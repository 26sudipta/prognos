import 'package:prognos/core/reminders/reminder_reconciler.dart';
import 'package:prognos/core/reminders/reminder_scheduler.dart';

/// A [ReminderScheduler] that never touches platform channels. It models the OS
/// pending set in memory, so `reconcile` can be exercised end-to-end in tests.
class FakeReminderScheduler extends ReminderScheduler {
  final Set<int> pending = {};

  /// Counts calls to [scheduleTest] — lets tests assert the reliability flow
  /// uses the real scheduled-alarm path (not an immediate show).
  int scheduleTestCount = 0;

  @override
  Future<void> init() async {}

  @override
  Stream<String> get taps => const Stream.empty();

  @override
  Future<String?> initialLaunchContestId() async => null;

  @override
  Future<void> schedule(DesiredReminder r) async => pending.add(r.notifId);

  @override
  Future<void> cancel(int notifId) async => pending.remove(notifId);

  @override
  Future<Set<int>> pendingIds() async => {...pending};

  @override
  Future<void> scheduleTest() async => scheduleTestCount++;

  @override
  Future<bool> requestNotificationsPermission() async => true;

  @override
  Future<bool> canScheduleExactAlarms() async => true;
}
