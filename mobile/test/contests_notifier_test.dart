import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/contests/contests_api.dart';
import 'package:prognos/core/contests/contests_providers.dart';
import 'package:prognos/core/db/app_database.dart';

import 'support/contests_fakes.dart';

/// Build a container wired to an in-memory DB and a fake API.
ProviderContainer _container(AppDatabase db, ContestsApi api) {
  final c = ProviderContainer(overrides: [
    appDatabaseProvider.overrideWithValue(db),
    contestsApiProvider.overrideWithValue(api),
  ]);
  addTearDown(c.dispose);
  return c;
}

void main() {
  test(
    'airplane mode: cached window still renders when the network is down',
    () async {
      final db = makeTestDb();
      addTearDown(db.close);
      await db.replaceContests([
        sampleContest(id: 'c1', startLocal: DateTime(2026, 5, 1, 10)),
      ]);

      final container = _container(db, FakeContestsApi(throwError: true));
      final result = await container.read(contestsProvider.future);

      // The list renders from cache despite the failing refresh.
      expect(result.contests.map((c) => c.id), ['c1']);
    },
  );

  test(
    'first-ever offline load degrades to an empty result, not an error',
    () async {
      final db = makeTestDb(); // empty cache
      addTearDown(db.close);

      final container = _container(db, FakeContestsApi(throwError: true));
      final result = await container.read(contestsProvider.future);

      expect(result.contests, isEmpty);
      expect(result.fromCacheOnly, isTrue);
    },
  );

  test('fresh fetch populates state and cache on first load', () async {
    final db = makeTestDb();
    addTearDown(db.close);

    final fresh = sampleContest(id: 'f1', startLocal: DateTime(2026, 6, 1, 10));
    final container = _container(
      db,
      FakeContestsApi(result: ContestsFetch([fresh], isStale: true)),
    );

    final result = await container.read(contestsProvider.future);
    expect(result.contests.map((c) => c.id), ['f1']);
    expect(result.isStale, isTrue);
    expect((await db.allContests()).map((c) => c.id), ['f1']);
  });
}
