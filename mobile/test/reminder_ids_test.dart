import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/reminders/reminder_ids.dart';

void main() {
  test('is deterministic across calls', () {
    expect(
      reminderNotifId('contest-abc', 60),
      reminderNotifId('contest-abc', 60),
    );
  });

  test('stays within Android 31-bit id range', () {
    for (final id in ['a', 'contest-xyz', 'x' * 64, '💥unicode']) {
      for (final lead in [5, 15, 60, 1440]) {
        final n = reminderNotifId(id, lead);
        expect(n, greaterThanOrEqualTo(0));
        expect(n, lessThanOrEqualTo(0x7FFFFFFF));
      }
    }
  });

  test('different lead / contest → different id', () {
    expect(reminderNotifId('c1', 60), isNot(reminderNotifId('c1', 15)));
    expect(reminderNotifId('c1', 60), isNot(reminderNotifId('c2', 60)));
  });
}
