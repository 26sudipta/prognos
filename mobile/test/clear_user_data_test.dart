import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/analytics/analytics_repository.dart';
import 'package:prognos/core/classrooms/classrooms_repository.dart';
import 'package:prognos/core/reminders/reminders_repository.dart';

import 'support/analytics_fakes.dart';
import 'support/classroom_fakes.dart';
import 'support/contests_fakes.dart';
import 'support/reminder_fakes.dart';

void main() {
  test('clearUserData wipes private analytics + reminders, keeps public contests',
      () async {
    final db = makeTestDb();
    addTearDown(db.close);

    // Seed a bit of everything for "User A".
    await db.replaceContests([
      sampleContest(id: 'c1', startLocal: DateTime.now().add(const Duration(days: 2))),
    ]);
    await AnalyticsRepository(
      FakeAnalyticsApi(dashboard: emptyDashboard(hasHandle: true)),
      db,
    ).fetchAndCache();
    final reminders = RemindersRepository(db, FakeReminderScheduler());
    await reminders.setStar('c1', true);
    await reminders.markOnboarded();
    await ClassroomsRepository(FakeClassroomsApi(classrooms: [sampleClassroom()]), db)
        .fetchList();

    // Sanity: private data present.
    expect(await AnalyticsRepository(FakeAnalyticsApi(), db).readCache(), isNotNull);
    expect(await db.starredContestIds(), isNotEmpty);
    expect(await db.readSetting('reminders_onboarded'), '1');

    // Sign-out cleanup.
    await db.clearUserData();

    // Private data gone…
    expect(await AnalyticsRepository(FakeAnalyticsApi(), db).readCache(), isNull);
    expect(await ClassroomsRepository(FakeClassroomsApi(), db).readCachedList(),
        isNull);
    expect(await db.starredContestIds(), isEmpty);
    expect(await db.scheduledReminderList(), isEmpty);
    expect(await db.readSetting('reminders_onboarded'), isNull);
    // …public contest cache preserved (re-usable by the next account).
    expect((await db.allContests()).map((c) => c.id), ['c1']);
  });
}
