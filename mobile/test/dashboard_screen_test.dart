import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/analytics/analytics_models.dart';
import 'package:prognos/core/analytics/analytics_providers.dart';
import 'package:prognos/core/contests/contests_providers.dart';
import 'package:prognos/theme/app_theme.dart';
import 'package:prognos/ui/dashboard/dashboard_screen.dart';

import 'support/analytics_fakes.dart';
import 'support/contests_fakes.dart';

DashboardData _dash() => DashboardData(
      heatmap: [
        HeatmapDay(date: '2026-06-25', count: 5, solved: 3),
        HeatmapDay(date: '2026-06-26', count: 12, solved: 8),
      ],
      currentStreak: 7,
      longestStreak: 23,
      totalSolved: 412,
      cfRating: 1724,
      hasVerifiedHandle: true,
      isSyncing: false,
    );

void main() {
  testWidgets('renders Overview then switches to Insights', (tester) async {
    final db = makeTestDb();
    addTearDown(db.close);

    final api = FakeAnalyticsApi(
      dashboard: _dash(),
      tagsData: const [
        TagStat(tag: 'dp', solvedCount: 40, attemptCount: 60, acceptanceRate: 0.66),
        TagStat(tag: 'graphs', solvedCount: 25, attemptCount: 50, acceptanceRate: 0.5),
      ],
      weaknessData: const [
        WeaknessSignal(
          tag: 'dp',
          signalType: 'neglected',
          score: 0.9,
          reason: 'Not practiced recently',
        ),
      ],
      ratingData: [
        RatingEntry(
          contestName: 'Round 1',
          oldRating: 1500,
          newRating: 1560,
          delta: 60,
          rank: 300,
          contestTime: DateTime.utc(2026, 5, 1),
        ),
        RatingEntry(
          contestName: 'Round 2',
          oldRating: 1560,
          newRating: 1724,
          delta: 164,
          rank: 120,
          contestTime: DateTime.utc(2026, 6, 1),
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          appDatabaseProvider.overrideWithValue(db),
          analyticsApiProvider.overrideWithValue(api),
        ],
        child: MaterialApp(
          theme: AppTheme.dark,
          home: const Scaffold(body: DashboardScreen()),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 50));

    // Overview: stat strip + heatmap render.
    expect(find.text('412'), findsOneWidget); // total solved
    expect(find.text('Activity'), findsOneWidget); // heatmap card
    expect(find.text('Overview'), findsOneWidget);

    // Switch to Insights → tag list renders.
    await tester.tap(find.text('Insights'));
    await tester.pump(const Duration(milliseconds: 50));
    expect(find.text('graphs'), findsOneWidget); // unique tag row
    expect(find.text('Focus Areas'), findsOneWidget);
  });

  testWidgets('shows the no-handle nudge when the account has no handle',
      (tester) async {
    final db = makeTestDb();
    addTearDown(db.close);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          appDatabaseProvider.overrideWithValue(db),
          analyticsApiProvider
              .overrideWithValue(FakeAnalyticsApi(dashboard: emptyDashboard())),
        ],
        child: MaterialApp(
          theme: AppTheme.dark,
          home: const Scaffold(body: DashboardScreen()),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.text('Link your Codeforces handle'), findsOneWidget);
  });
}
