import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/app.dart';
import 'package:prognos/core/analytics/analytics_providers.dart';
import 'package:prognos/core/classrooms/classrooms_providers.dart';
import 'package:prognos/core/contests/contests_providers.dart';
import 'package:prognos/core/reminders/reminders_providers.dart';
import 'package:prognos/core/storage/secure_store.dart';
import 'package:prognos/theme/app_theme.dart';
import 'package:prognos/theme/cf_rating.dart';
import 'package:prognos/ui/shell/home_shell.dart';

import 'support/analytics_fakes.dart';
import 'support/classroom_fakes.dart';
import 'support/contests_fakes.dart';
import 'support/reminder_fakes.dart';

/// Secure store with no stored session — makes launch restore deterministically
/// resolve to "logged out" without touching the platform keystore plugin.
class _EmptySecureStore extends SecureStore {
  _EmptySecureStore() : super(const FlutterSecureStorage());
  @override
  Future<String?> readRefreshToken() async => null;
  @override
  Future<void> writeRefreshToken(String token) async {}
  @override
  Future<void> clear() async {}
}

void main() {
  testWidgets('boots to the login screen when there is no session', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [secureStoreProvider.overrideWithValue(_EmptySecureStore())],
        child: const PrognosApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Continue with Google'), findsOneWidget);
  });

  testWidgets('shell renders three tabs and switches', (tester) async {
    // The Contests tab (built eagerly by the IndexedStack) needs an in-memory
    // DB + a fake API so it never touches the platform DB or the network.
    final db = makeTestDb();
    addTearDown(db.close);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          appDatabaseProvider.overrideWithValue(db),
          contestsApiProvider.overrideWithValue(FakeContestsApi()),
          analyticsApiProvider.overrideWithValue(FakeAnalyticsApi()),
          classroomsApiProvider.overrideWithValue(FakeClassroomsApi()),
          reminderSchedulerProvider.overrideWithValue(FakeReminderScheduler()),
        ],
        child: MaterialApp(theme: AppTheme.dark, home: const HomeShell()),
      ),
    );
    // Let the (empty) contest load resolve without waiting on the shimmer.
    await tester.pump(const Duration(milliseconds: 50));

    // Bottom-nav labels present; Dashboard is the default tab (AppBar title).
    expect(find.text('Dashboard'), findsWidgets);
    expect(find.text('Contests'), findsOneWidget);
    expect(find.text('Classes'), findsWidgets);

    await tester.tap(find.byIcon(Icons.event_outlined));
    await tester.pump(const Duration(milliseconds: 50));
    // The real Contests screen now renders (empty window → empty state).
    expect(find.text('No upcoming contests'), findsOneWidget);
  });

  test('CF rating ladder matches the web thresholds', () {
    expect(CfRating.rank(null), 'Unrated');
    expect(CfRating.rank(1199), 'Newbie');
    expect(CfRating.rank(1200), 'Pupil');
    expect(CfRating.rank(1600), 'Expert');
    expect(CfRating.rank(2400), 'Grandmaster+');
    expect(CfRating.color(2400), const Color(0xFFF44336));
  });
}
