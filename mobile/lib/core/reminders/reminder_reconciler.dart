import '../db/app_database.dart';
import 'reminder_ids.dart';

/// A single reminder to fire: which contest, how long before, and the exact
/// (UTC) instant. `notifId` is the deterministic 31-bit ID.
class DesiredReminder {
  const DesiredReminder({
    required this.notifId,
    required this.contest,
    required this.leadMinutes,
    required this.fireAt,
  });

  final int notifId;
  final Contest contest;
  final int leadMinutes;
  final DateTime fireAt; // UTC
}

/// iOS schedules at most 64 pending notifications; keep headroom.
const int kIosPendingCap = 48;

/// Pure computation of the desired reminder set — no I/O, fully testable.
///
/// A contest earns reminders when it is **starred** OR its **platform rule** is
/// enabled, it hasn't started yet, and the `start − lead` instant is still in
/// the future. IDs are deterministic so the caller can diff against what the OS
/// already has scheduled.
List<DesiredReminder> computeDesiredReminders({
  required List<Contest> contests,
  required Set<String> starredIds,
  required Set<String> enabledPlatforms,
  required List<int> leadMinutes,
  required DateTime nowUtc,
}) {
  final desired = <DesiredReminder>[];
  for (final c in contests) {
    final wanted = starredIds.contains(c.id) || enabledPlatforms.contains(c.platform);
    if (!wanted) continue;
    if (!c.startTime.isAfter(nowUtc)) continue; // already started/ended

    for (final lead in leadMinutes) {
      final fireAt = c.startTime.subtract(Duration(minutes: lead));
      if (!fireAt.isAfter(nowUtc)) continue; // lead already passed
      desired.add(DesiredReminder(
        notifId: reminderNotifId(c.id, lead),
        contest: c,
        leadMinutes: lead,
        fireAt: fireAt,
      ));
    }
  }
  return desired;
}

/// Every notification id the current cache could legitimately own — one per
/// (cached contest, lead). Reconcile may only cancel ids in this set; an alarm
/// whose contest has aged out of the fetched window is *not* here, so it is left
/// armed rather than wiped.
Set<int> managedReminderIds({
  required List<Contest> contests,
  required List<int> leadMinutes,
}) =>
    {
      for (final c in contests)
        for (final lead in leadMinutes) reminderNotifId(c.id, lead),
    };

/// Apply the iOS pending cap: keep the soonest [kIosPendingCap] by fire time.
/// Slots free up as contests pass, so this is recomputed on every foreground.
List<DesiredReminder> capForIos(List<DesiredReminder> desired) {
  if (desired.length <= kIosPendingCap) return desired;
  final sorted = [...desired]..sort((a, b) => a.fireAt.compareTo(b.fireAt));
  return sorted.sublist(0, kIosPendingCap);
}

/// The schedule/cancel deltas needed to move the OS from [pendingIds] (what is
/// actually scheduled, per `pendingNotificationRequests()`) to [desired].
///
/// Reconciling against the **OS** (not our ledger) keeps us correct after a
/// reboot, an iOS eviction, or the user clearing notifications.
class ReminderDiff {
  const ReminderDiff({required this.toSchedule, required this.toCancel});

  /// Desired reminders not currently scheduled.
  final List<DesiredReminder> toSchedule;

  /// IDs currently scheduled by us but no longer desired.
  final List<int> toCancel;
}

ReminderDiff diffReminders({
  required List<DesiredReminder> desired,
  required Set<int> pendingIds,
  required Set<int> managedIds,
}) {
  final desiredById = {for (final d in desired) d.notifId: d};

  final toSchedule = [
    for (final d in desired)
      if (!pendingIds.contains(d.notifId)) d,
  ];
  // Only cancel an alarm we can *prove* is no longer wanted: its contest is
  // still in the cache ([managedIds]) but dropped out of [desired] (un-starred,
  // rule disabled, started, or its lead passed). A pending alarm whose contest
  // has aged out of the fetched window is NOT in managedIds, so it is left armed
  // — it already holds the correct fire time. Cancelling those was why
  // out-of-window reminders silently never fired.
  final toCancel = [
    for (final id in pendingIds)
      if (managedIds.contains(id) && !desiredById.containsKey(id)) id,
  ];
  return ReminderDiff(toSchedule: toSchedule, toCancel: toCancel);
}
