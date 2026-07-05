import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/contests/contest_format.dart';

import 'support/contests_fakes.dart';

void main() {
  group('formatDuration', () {
    test('formats hours and minutes', () {
      expect(formatDuration(7200), '2h');
      expect(formatDuration(8100), '2h 15m');
      expect(formatDuration(2700), '45m');
    });
  });

  group('groupByUrgency', () {
    // Anchor "now" to a fixed LOCAL wall-clock so lane math is deterministic
    // regardless of the machine timezone. 2026-03-10 is a Tuesday.
    final nowLocal = DateTime(2026, 3, 10, 12, 0);
    final now = nowLocal.toUtc();

    test('classifies live / today / this-week / later', () {
      final contests = [
        sampleContest(id: 'live', startLocal: DateTime(2026, 3, 10, 11, 30)),
        sampleContest(id: 'today', startLocal: DateTime(2026, 3, 10, 20, 0)),
        sampleContest(id: 'thisweek', startLocal: DateTime(2026, 3, 12, 10, 0)),
        sampleContest(id: 'later', startLocal: DateTime(2026, 4, 1, 10, 0)),
      ];

      final lanes = groupByUrgency(contests, now);
      final byLane = {for (final l in lanes) l.lane: l.contests};

      expect(byLane[UrgencyLane.live]!.single.id, 'live');
      expect(byLane[UrgencyLane.today]!.single.id, 'today');
      expect(byLane[UrgencyLane.thisWeek]!.single.id, 'thisweek');
      expect(byLane[UrgencyLane.later]!.single.id, 'later');
    });

    test('omits ended contests', () {
      final ended = sampleContest(
        id: 'ended',
        startLocal: DateTime(2026, 3, 9, 10, 0),
        duration: const Duration(hours: 1),
      );
      expect(groupByUrgency([ended], now), isEmpty);
    });
  });

  group('contestsOnLocalDay', () {
    test('groups by local calendar day, not UTC', () {
      // 23:30 local — in many timezones this is a different UTC calendar day,
      // yet it must group under its LOCAL day.
      final lateNight =
          sampleContest(id: 'late', startLocal: DateTime(2026, 7, 4, 23, 30));

      final onThe4th = contestsOnLocalDay([lateNight], DateTime(2026, 7, 4));
      final onThe5th = contestsOnLocalDay([lateNight], DateTime(2026, 7, 5));

      expect(onThe4th.single.id, 'late');
      expect(onThe5th, isEmpty);
    });
  });

  group('nextContest', () {
    final now = DateTime(2026, 3, 10, 12, 0).toUtc();

    test('prefers a live contest over an upcoming one', () {
      final live = sampleContest(id: 'live', startLocal: DateTime(2026, 3, 10, 11, 30));
      final soon = sampleContest(id: 'soon', startLocal: DateTime(2026, 3, 10, 14, 0));
      expect(nextContest([soon, live], now)!.id, 'live');
    });

    test('returns the soonest upcoming when none live', () {
      final a = sampleContest(id: 'a', startLocal: DateTime(2026, 3, 11, 10, 0));
      final b = sampleContest(id: 'b', startLocal: DateTime(2026, 3, 10, 18, 0));
      expect(nextContest([a, b], now)!.id, 'b');
    });

    test('returns null when everything has ended', () {
      final ended = sampleContest(
        id: 'e',
        startLocal: DateTime(2026, 3, 9, 10, 0),
        duration: const Duration(hours: 1),
      );
      expect(nextContest([ended], now), isNull);
    });
  });

  test('distinctPlatforms is sorted and deduplicated', () {
    final contests = [
      sampleContest(id: '1', platform: 'atcoder.jp', startLocal: DateTime(2026, 3, 10, 10)),
      sampleContest(id: '2', platform: 'codeforces.com', startLocal: DateTime(2026, 3, 10, 11)),
      sampleContest(id: '3', platform: 'atcoder.jp', startLocal: DateTime(2026, 3, 10, 12)),
    ];
    expect(distinctPlatforms(contests), ['atcoder.jp', 'codeforces.com']);
  });
}
