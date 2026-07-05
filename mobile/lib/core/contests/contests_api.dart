import 'package:dio/dio.dart';

import '../db/app_database.dart';

/// Result of one `GET /contests` fetch: the window plus the server's staleness
/// flag (true when the backend's own CLIST sync is lagging).
class ContestsFetch {
  const ContestsFetch(this.contests, {required this.isStale});

  final List<Contest> contests;
  final bool isStale;
}

/// Thin wrapper over `GET /api/v1/contests`. Uses the **authed** Dio (Bearer +
/// refresh-on-401). Parses timestamps as UTC-aware instants — the backend sends
/// tz-offset ISO 8601, and grouping/countdowns must convert to local later.
class ContestsApi {
  ContestsApi(this._dio);

  final Dio _dio;

  /// Fetch a window of contests. Defaults to a 30-day forward window (live +
  /// upcoming), matching the reminder cache window in the mobile plan.
  Future<ContestsFetch> fetchContests({
    List<String>? platform,
    DateTime? fromDt,
    DateTime? toDt,
    int limit = 200,
  }) async {
    final now = DateTime.now().toUtc();
    final from = (fromDt ?? now).toUtc();
    final to = (toDt ?? now.add(const Duration(days: 30))).toUtc();

    final res = await _dio.get<Map<String, dynamic>>(
      '/contests',
      queryParameters: {
        'from_dt': from.toIso8601String(),
        'to_dt': to.toIso8601String(),
        'limit': limit,
        if (platform != null && platform.isNotEmpty) 'platform': platform,
      },
      // FastAPI expects a repeated key (`?platform=a&platform=b`) for its
      // `list[str] = Query()` param. `ListFormat.multi` produces exactly that;
      // `multiCompatible` would send `platform[]=…` and the filter would break.
      options: Options(listFormat: ListFormat.multi),
    );

    final data = res.data ?? const {};
    final rawList = (data['contests'] as List<dynamic>? ?? const []);
    final contests = rawList
        .map((e) => _parseContest(e as Map<String, dynamic>))
        .toList(growable: false);
    return ContestsFetch(contests, isStale: data['is_stale'] == true);
  }
}

/// Map one API contest object → a drift [Contest] row. `cachedAt` is stamped
/// at parse time (used for offline cache-age reasoning).
Contest _parseContest(Map<String, dynamic> j) => Contest(
      id: j['id'] as String,
      clistId: (j['clist_id'] as num).toInt(),
      platform: j['platform'] as String,
      name: j['name'] as String,
      startTime: DateTime.parse(j['start_time'] as String).toUtc(),
      endTime: DateTime.parse(j['end_time'] as String).toUtc(),
      durationSeconds: (j['duration_seconds'] as num).toInt(),
      url: j['url'] as String,
      lastSyncedAt: DateTime.parse(j['last_synced_at'] as String).toUtc(),
      cachedAt: DateTime.now().toUtc(),
    );
