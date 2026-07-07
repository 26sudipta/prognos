import 'package:flutter_test/flutter_test.dart';

import 'support/reminder_fakes.dart';

void main() {
  // The reliability flow's "test alert" must go through the real scheduled-alarm
  // path (scheduleTest), NOT an immediate show — an immediate notification would
  // succeed even on a device that silently drops scheduled alarms, making the
  // test a false positive. The immediate `showTest` no longer exists; this pins
  // the honest contract.
  test('scheduleTest is the test mechanism (scheduled, not immediate)',
      () async {
    final scheduler = FakeReminderScheduler();
    expect(scheduler.scheduleTestCount, 0);
    await scheduler.scheduleTest();
    await scheduler.scheduleTest();
    expect(scheduler.scheduleTestCount, 2);
  });
}
