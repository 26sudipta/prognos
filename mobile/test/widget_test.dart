import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/app.dart';
import 'package:prognos/theme/cf_rating.dart';

void main() {
  testWidgets('app boots to the three-tab shell', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: PrognosApp()));
    await tester.pump();

    // Bottom-nav labels + selected Dashboard tab title both render "Dashboard".
    expect(find.text('Dashboard'), findsWidgets);
    expect(find.text('Contests'), findsOneWidget);
    expect(find.text('Leaderboard'), findsOneWidget);
  });

  testWidgets('switching tabs shows the Contests screen', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: PrognosApp()));
    await tester.pump();

    await tester.tap(find.byIcon(Icons.event_outlined));
    // Not pumpAndSettle: the shimmer skeletons animate forever by design.
    await tester.pump();

    expect(find.textContaining('Contests — arriving in M2'), findsOneWidget);
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
