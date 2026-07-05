import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/classrooms/classroom_models.dart';
import 'package:prognos/core/classrooms/classrooms_repository.dart';

import 'support/classroom_fakes.dart';
import 'support/contests_fakes.dart';

void main() {
  test('classroom + leaderboard round-trip through JSON', () {
    final c = Classroom.fromJson(sampleClassroom().toJson());
    expect(c.name, 'CP 101');
    expect(c.isTeacher, isTrue);

    final b = Leaderboard.fromJson(sampleBoard().toJson());
    expect(b.entries.single.cfHandle, 'tourist');
    expect(b.entries.single.topTags, ['dp', 'graphs']);
    expect(b.entries.single.isMe, isTrue);
  });

  test('fetchList caches; readCachedList reads it back', () async {
    final db = makeTestDb();
    addTearDown(db.close);
    final repo = ClassroomsRepository(
      FakeClassroomsApi(classrooms: [sampleClassroom(id: 'a', name: 'A')]),
      db,
    );

    expect(await repo.readCachedList(), isNull); // nothing cached yet
    final fetched = await repo.fetchList();
    expect(fetched.single.name, 'A');

    final cached = await repo.readCachedList();
    expect(cached!.single.id, 'a');
  });

  test('leaderboard cache lets the board render offline', () async {
    final db = makeTestDb();
    addTearDown(db.close);

    // Online fetch seeds the cache.
    await ClassroomsRepository(FakeClassroomsApi(), db).fetchLeaderboard('cl1');

    // Offline: fetch throws, but the cache is present.
    final offline = ClassroomsRepository(
        FakeClassroomsApi(throwError: true), db);
    final cached = await offline.readCachedLeaderboard('cl1');
    expect(cached, isNotNull);
    expect(cached!.entries.single.cfHandle, 'tourist');
  });
}
