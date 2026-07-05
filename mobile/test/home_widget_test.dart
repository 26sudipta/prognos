import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/widget/home_widget_service.dart';

import 'support/contests_fakes.dart';

void main() {
  final now = DateTime.utc(2026, 3, 10, 12, 0);

  test('empty cache → placeholder title and no streak', () async {
    final db = makeTestDb();
    addTearDown(db.close);
    final p = await buildWidgetPayload(db, nowUtc: now);
    expect(p['next_title'], 'No upcoming contests');
    expect(p['next_subtitle'], '');
    expect(p['streak'], '—');
  });

  test('next contest + streak render into flat values', () async {
    final db = makeTestDb();
    addTearDown(db.close);
    await db.replaceContests([
      sampleContest(
        id: 'c1',
        name: 'Round 950',
        platform: 'codeforces.com',
        startLocal: now.add(const Duration(hours: 3, minutes: 12)).toLocal(),
      ),
    ]);
    await db.writeSetting('analytics.dashboard',
        jsonEncode({'current_streak': 7, 'heatmap': []}));

    final p = await buildWidgetPayload(db, nowUtc: now);
    expect(p['next_title'], 'Round 950');
    expect(p['next_subtitle'], contains('Codeforces'));
    expect(p['next_subtitle'], contains('in 3h'));
    expect(p['streak'], '7');
  });

  test('a live contest shows LIVE', () async {
    final db = makeTestDb();
    addTearDown(db.close);
    await db.replaceContests([
      sampleContest(
        id: 'live',
        startLocal: now.subtract(const Duration(minutes: 20)).toLocal(),
        duration: const Duration(hours: 2),
      ),
    ]);
    final p = await buildWidgetPayload(db, nowUtc: now);
    expect(p['next_subtitle'], contains('LIVE'));
  });
}
