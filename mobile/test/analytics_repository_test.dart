import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/analytics/analytics_models.dart';
import 'package:prognos/core/analytics/analytics_repository.dart';

import 'support/analytics_fakes.dart';
import 'support/contests_fakes.dart';

void main() {
  test('readCache returns null before anything is cached', () async {
    final db = makeTestDb();
    addTearDown(db.close);
    final repo = AnalyticsRepository(FakeAnalyticsApi(), db);
    expect(await repo.readCache(), isNull);
  });

  test('fetchAndCache stores every section; readCache reads it back', () async {
    final db = makeTestDb();
    addTearDown(db.close);
    final api = FakeAnalyticsApi(
      dashboard: emptyDashboard(hasHandle: true).copyWithSolved(412),
      tagsData: const [
        TagStat(tag: 'dp', solvedCount: 40, attemptCount: 60, acceptanceRate: 0.66),
      ],
      recsData: const RecommendationSet(recommendations: [
        Recommendation(
          problemName: 'P',
          tag: 'dp',
          difficulty: 1500,
          url: 'https://cf/1',
          reason: 'r',
          position: 1,
        ),
      ]),
    );
    final repo = AnalyticsRepository(api, db);

    final fresh = await repo.fetchAndCache();
    expect(fresh.fromCache, isFalse);
    expect(fresh.dashboard!.totalSolved, 412);

    final cached = await repo.readCache();
    expect(cached, isNotNull);
    expect(cached!.fromCache, isTrue);
    expect(cached.dashboard!.totalSolved, 412);
    expect(cached.tags.single.tag, 'dp');
    expect(cached.recommendations!.recommendations.single.problemName, 'P');
  });

  test('a failing fetch throws but leaves the cache intact (offline)', () async {
    final db = makeTestDb();
    addTearDown(db.close);

    // Seed a good cache.
    await AnalyticsRepository(
      FakeAnalyticsApi(dashboard: emptyDashboard(hasHandle: true).copyWithSolved(99)),
      db,
    ).fetchAndCache();

    // Now the network is down.
    final offlineRepo = AnalyticsRepository(FakeAnalyticsApi(throwError: true), db);
    await expectLater(offlineRepo.fetchAndCache(), throwsA(anything));

    final cached = await offlineRepo.readCache();
    expect(cached!.dashboard!.totalSolved, 99); // preserved
  });
}

extension on DashboardData {
  DashboardData copyWithSolved(int solved) => DashboardData(
        heatmap: heatmap,
        currentStreak: currentStreak,
        longestStreak: longestStreak,
        totalSolved: solved,
        cfRating: cfRating,
        hasVerifiedHandle: hasVerifiedHandle,
        isSyncing: isSyncing,
      );
}
