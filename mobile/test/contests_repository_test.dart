import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/contests/contests_api.dart';
import 'package:prognos/core/contests/contests_repository.dart';

import 'support/contests_fakes.dart';

void main() {
  test('fetchAndReplace overwrites the cache on success', () async {
    final db = makeTestDb();
    addTearDown(db.close);

    // Seed an old window.
    await db.replaceContests([
      sampleContest(id: 'old', startLocal: DateTime(2026, 1, 1, 10)),
    ]);

    final fresh = sampleContest(id: 'new', startLocal: DateTime(2026, 2, 2, 10));
    final repo = ContestsRepository(
      FakeContestsApi(result: ContestsFetch([fresh], isStale: false)),
      db,
    );

    final result = await repo.fetchAndReplace();

    expect(result.contests.map((c) => c.id), ['new']);
    expect(result.fromCacheOnly, isFalse);
    // Cache now equals the fresh window (old row dropped).
    expect((await db.allContests()).map((c) => c.id), ['new']);
  });

  test(
    'a failing fetch throws but leaves the cache intact (offline guarantee)',
    () async {
      final db = makeTestDb();
      addTearDown(db.close);

      final cached = sampleContest(
        id: 'cached',
        startLocal: DateTime(2026, 3, 3, 10),
      );
      await db.replaceContests([cached]);

      final repo = ContestsRepository(
        FakeContestsApi(throwError: true),
        db,
      );

      // The network call must surface as an error to the caller…
      await expectLater(repo.fetchAndReplace(), throwsA(anything));
      // …but must NOT clear or mutate the cache.
      expect((await db.allContests()).map((c) => c.id), ['cached']);
      expect((await repo.readCache()).map((c) => c.id), ['cached']);
    },
  );
}
