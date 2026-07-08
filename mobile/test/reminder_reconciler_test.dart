import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/reminders/reminder_ids.dart';
import 'package:prognos/core/reminders/reminder_reconciler.dart';

import 'support/contests_fakes.dart';

void main() {
  final now = DateTime.utc(2026, 3, 10, 12, 0);

  // A contest starting `mins` minutes from `now`.
  contestStartingIn(int mins, {String id = 'c', String platform = 'codeforces.com'}) =>
      sampleContest(
        id: id,
        platform: platform,
        startLocal: now.add(Duration(minutes: mins)).toLocal(),
      );

  group('computeDesiredReminders', () {
    test('a starred contest gets a reminder per lead whose time is still ahead',
        () {
      final c = contestStartingIn(90, id: 'star'); // 90 min out
      final desired = computeDesiredReminders(
        contests: [c],
        starredIds: {'star'},
        enabledPlatforms: const {},
        leadMinutes: const [60, 15],
        nowUtc: now,
      );
      // 60m lead → fires in 30 min (ok); 15m lead → fires in 75 min (ok).
      expect(desired.length, 2);
      expect(
        desired.map((d) => d.notifId).toSet(),
        {reminderNotifId('star', 60), reminderNotifId('star', 15)},
      );
    });

    test('drops a lead whose fire time has already passed', () {
      final c = contestStartingIn(30, id: 'soon'); // 30 min out
      final desired = computeDesiredReminders(
        contests: [c],
        starredIds: {'soon'},
        enabledPlatforms: const {},
        leadMinutes: const [60, 15],
        nowUtc: now,
      );
      // 60m lead would fire 30 min ago → dropped; only the 15m lead remains.
      expect(desired.map((d) => d.leadMinutes), [15]);
    });

    test('platform rule schedules; unrelated contests do not', () {
      final cf = contestStartingIn(120, id: 'cf', platform: 'codeforces.com');
      final ac = contestStartingIn(120, id: 'ac', platform: 'atcoder.jp');
      final desired = computeDesiredReminders(
        contests: [cf, ac],
        starredIds: const {},
        enabledPlatforms: {'codeforces.com'},
        leadMinutes: const [60],
        nowUtc: now,
      );
      expect(desired.map((d) => d.contest.id), ['cf']);
    });

    test('ignores already-started contests', () {
      final started = contestStartingIn(-10, id: 'live');
      final desired = computeDesiredReminders(
        contests: [started],
        starredIds: {'live'},
        enabledPlatforms: const {},
        leadMinutes: const [60, 15],
        nowUtc: now,
      );
      expect(desired, isEmpty);
    });
  });

  group('diffReminders', () {
    test('schedules the missing; cancels an in-cache contest no longer wanted', () {
      final star = contestStartingIn(90, id: 'star');
      final dropped = contestStartingIn(120, id: 'dropped'); // cached, un-starred
      final desired = computeDesiredReminders(
        contests: [star, dropped],
        starredIds: {'star'}, // 'dropped' is no longer starred
        enabledPlatforms: const {},
        leadMinutes: const [60, 15],
        nowUtc: now,
      );
      final id60 = reminderNotifId('star', 60);
      final id15 = reminderNotifId('star', 15);
      final droppedId = reminderNotifId('dropped', 60);
      final managed = managedReminderIds(
        contests: [star, dropped],
        leadMinutes: const [60, 15],
      );

      // OS has star's 60m alarm + a stale alarm for the now-unstarred 'dropped'.
      final diff = diffReminders(
        desired: desired,
        pendingIds: {id60, droppedId},
        managedIds: managed,
      );

      expect(diff.toSchedule.map((d) => d.notifId), [id15]); // missing
      expect(diff.toCancel, [droppedId]); // cached but no longer wanted
    });

    test('leaves alarms armed for contests that aged out of the cache window', () {
      final star = contestStartingIn(90, id: 'star');
      final desired = computeDesiredReminders(
        contests: [star],
        starredIds: {'star'},
        enabledPlatforms: const {},
        leadMinutes: const [60, 15],
        nowUtc: now,
      );
      // An alarm for a contest no longer in the cache (aged past the 30-day window).
      const outOfWindowId = 424243;
      final managed =
          managedReminderIds(contests: [star], leadMinutes: const [60, 15]);

      final diff = diffReminders(
        desired: desired,
        pendingIds: {
          reminderNotifId('star', 60),
          reminderNotifId('star', 15),
          outOfWindowId,
        },
        managedIds: managed,
      );

      // The out-of-window alarm is preserved, not wiped — this is the fix.
      expect(diff.toCancel, isEmpty);
    });
  });

  group('capForIos', () {
    test('keeps only the soonest kIosPendingCap by fire time', () {
      final many = List.generate(
        kIosPendingCap + 10,
        (i) => contestStartingIn(60 + i * 60, id: 'c$i'),
      );
      final desired = computeDesiredReminders(
        contests: many,
        starredIds: {for (final c in many) c.id},
        enabledPlatforms: const {},
        leadMinutes: const [15],
        nowUtc: now,
      );
      expect(desired.length, kIosPendingCap + 10);

      final capped = capForIos(desired);
      expect(capped.length, kIosPendingCap);
      // Soonest kept: the earliest fire time must survive, the latest must not.
      final keptIds = capped.map((d) => d.notifId).toSet();
      final byFire = [...desired]..sort((a, b) => a.fireAt.compareTo(b.fireAt));
      expect(keptIds.contains(byFire.first.notifId), isTrue);
      expect(keptIds.contains(byFire.last.notifId), isFalse);
    });
  });
}
