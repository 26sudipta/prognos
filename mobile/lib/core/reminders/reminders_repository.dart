import 'package:flutter/foundation.dart';

import '../db/app_database.dart';
import 'reminder_reconciler.dart';
import 'reminder_scheduler.dart';

/// Default lead times (minutes): one hour and fifteen minutes before start.
const List<int> kDefaultLeadMinutes = [60, 15];
const String _kLeadSetting = 'reminder_lead_minutes';
const String _kOnboardedSetting = 'reminders_onboarded';

/// Ties together drift state (stars / rules / lead times / ledger), the pure
/// reconciler, and the OS scheduler. The single entry point is [reconcile],
/// called after any change and on app foreground.
class RemindersRepository {
  RemindersRepository(this._db, this._scheduler);

  final AppDatabase _db;
  final ReminderScheduler _scheduler;

  Future<Set<String>> starredIds() => _db.starredContestIds();
  Future<List<PlatformRule>> platformRules() => _db.platformRulesList();
  Future<List<ScheduledReminder>> upcomingReminders() =>
      _db.scheduledReminderList();

  Future<List<int>> leadMinutes() async {
    final raw = await _db.readSetting(_kLeadSetting);
    if (raw == null || raw.isEmpty) return kDefaultLeadMinutes;
    final parsed = raw
        .split(',')
        .map((s) => int.tryParse(s.trim()))
        .whereType<int>()
        .toList();
    return parsed.isEmpty ? kDefaultLeadMinutes : parsed;
  }

  Future<void> setLeadMinutes(List<int> minutes) async {
    final sorted = [...minutes]..sort((a, b) => b.compareTo(a));
    await _db.writeSetting(_kLeadSetting, sorted.join(','));
    await reconcile();
  }

  Future<bool> isOnboarded() async =>
      (await _db.readSetting(_kOnboardedSetting)) == '1';

  Future<void> markOnboarded() => _db.writeSetting(_kOnboardedSetting, '1');

  Future<void> setStar(String contestId, bool starred) async {
    await _db.setStarred(contestId, starred);
    await reconcile();
  }

  Future<void> setPlatformRule(String platform, bool enabled) async {
    await _db.setPlatformRule(platform, enabled);
    await reconcile();
  }

  /// Recompute the desired reminder set from current state, diff it against what
  /// the OS actually has scheduled, then schedule/cancel the deltas and refresh
  /// the ledger. Idempotent — safe to call repeatedly (app open, foreground,
  /// after any toggle).
  Future<void> reconcile() async {
    final contests = await _db.allContests();
    final starred = await _db.starredContestIds();
    final enabled = await _db.enabledPlatforms();
    final leads = await leadMinutes();

    var desired = computeDesiredReminders(
      contests: contests,
      starredIds: starred,
      enabledPlatforms: enabled,
      leadMinutes: leads,
      nowUtc: DateTime.now().toUtc(),
    );
    if (defaultTargetPlatform == TargetPlatform.iOS) {
      desired = capForIos(desired);
    }

    final pending = await _scheduler.pendingIds();
    final diff = diffReminders(
      desired: desired,
      pendingIds: pending,
      // Only alarms whose contest is still cached may be cancelled — an alarm for
      // a contest that aged out of the 30-day window stays armed so it still fires.
      managedIds: managedReminderIds(contests: contests, leadMinutes: leads),
    );

    for (final id in diff.toCancel) {
      await _scheduler.cancel(id);
    }
    for (final r in diff.toSchedule) {
      await _scheduler.schedule(r);
    }

    // Ledger = intent (drives the settings "upcoming" list). The OS pending set
    // remains the reconcile source of truth.
    await _db.replaceScheduledReminders([
      for (final d in desired)
        ScheduledReminder(
          notifId: d.notifId,
          contestId: d.contest.id,
          leadMinutes: d.leadMinutes,
          fireAt: d.fireAt,
        ),
    ]);
  }
}
