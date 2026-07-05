import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/reminders/reminder_ids.dart';
import 'package:prognos/core/reminders/reminders_repository.dart';

import 'support/contests_fakes.dart';
import 'support/reminder_fakes.dart';

void main() {
  test('reconcile schedules reminders for a starred contest and updates ledger',
      () async {
    final db = makeTestDb();
    addTearDown(db.close);
    final scheduler = FakeReminderScheduler();
    final repo = RemindersRepository(db, scheduler);

    // A contest well in the future so both default leads (60/15) are ahead.
    final c = sampleContest(
      id: 'cf1',
      startLocal: DateTime.now().add(const Duration(days: 2)),
    );
    await db.replaceContests([c]);

    await repo.setStar('cf1', true); // triggers reconcile

    expect(scheduler.pending, {
      reminderNotifId('cf1', 60),
      reminderNotifId('cf1', 15),
    });
    // Ledger mirrors the intent for the settings "upcoming" list.
    expect((await repo.upcomingReminders()).length, 2);
  });

  test('un-starring cancels the scheduled reminders', () async {
    final db = makeTestDb();
    addTearDown(db.close);
    final scheduler = FakeReminderScheduler();
    final repo = RemindersRepository(db, scheduler);

    final c = sampleContest(
      id: 'cf1',
      startLocal: DateTime.now().add(const Duration(days: 2)),
    );
    await db.replaceContests([c]);

    await repo.setStar('cf1', true);
    expect(scheduler.pending, isNotEmpty);

    await repo.setStar('cf1', false);
    expect(scheduler.pending, isEmpty);
    expect(await repo.upcomingReminders(), isEmpty);
  });

  test('a platform rule schedules every contest on that platform', () async {
    final db = makeTestDb();
    addTearDown(db.close);
    final scheduler = FakeReminderScheduler();
    final repo = RemindersRepository(db, scheduler);

    await db.replaceContests([
      sampleContest(
        id: 'cf1',
        platform: 'codeforces.com',
        startLocal: DateTime.now().add(const Duration(days: 2)),
      ),
      sampleContest(
        id: 'ac1',
        platform: 'atcoder.jp',
        startLocal: DateTime.now().add(const Duration(days: 2)),
      ),
    ]);

    await repo.setLeadMinutes([60]); // single lead for a clean count
    await repo.setPlatformRule('codeforces.com', true);

    expect(scheduler.pending, {reminderNotifId('cf1', 60)});
  });
}
