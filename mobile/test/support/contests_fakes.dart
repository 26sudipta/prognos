import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:prognos/core/contests/contests_api.dart';
import 'package:prognos/core/db/app_database.dart';

/// In-memory drift DB for tests — no `sqlite3_flutter_libs` / file I/O.
AppDatabase makeTestDb() => AppDatabase.forTesting(NativeDatabase.memory());

/// Build a [Contest] row from **local** wall-clock times, converting to the
/// UTC instants the app stores. Keeps tests deterministic across machine
/// timezones (we assert on local grouping).
Contest sampleContest({
  required String id,
  String platform = 'codeforces.com',
  String name = 'Sample Round',
  required DateTime startLocal,
  Duration duration = const Duration(hours: 2),
}) {
  final start = startLocal.toUtc();
  final end = startLocal.add(duration).toUtc();
  return Contest(
    id: id,
    clistId: id.hashCode,
    platform: platform,
    name: name,
    startTime: start,
    endTime: end,
    durationSeconds: duration.inSeconds,
    url: 'https://example.com/$id',
    lastSyncedAt: DateTime.now().toUtc(),
    cachedAt: DateTime.now().toUtc(),
  );
}

/// Fake [ContestsApi] that either returns a fixed window or throws (to simulate
/// being offline). Never touches the network.
class FakeContestsApi extends ContestsApi {
  FakeContestsApi({this.result, this.throwError = false}) : super(Dio());

  final ContestsFetch? result;
  final bool throwError;
  int callCount = 0;

  @override
  Future<ContestsFetch> fetchContests({
    List<String>? platform,
    DateTime? fromDt,
    DateTime? toDt,
    int limit = 200,
  }) async {
    callCount++;
    if (throwError) {
      throw DioException(
        requestOptions: RequestOptions(path: '/contests'),
        type: DioExceptionType.connectionError,
      );
    }
    return result ?? const ContestsFetch([], isStale: false);
  }
}
