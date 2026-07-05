import 'dart:convert';

import '../db/app_database.dart';
import 'analytics_api.dart';
import 'analytics_models.dart';

/// Combined analytics snapshot for the Dashboard tab. Any field may be null/empty
/// (no handle, sync not run). [fromCache] is true when the visible data came
/// from the offline cache because a network refresh failed.
class AnalyticsState {
  const AnalyticsState({
    this.dashboard,
    this.tags = const [],
    this.rating = const [],
    this.weaknesses = const [],
    this.recommendations,
    this.fromCache = false,
  });

  final DashboardData? dashboard;
  final List<TagStat> tags;
  final List<RatingEntry> rating;
  final List<WeaknessSignal> weaknesses;
  final RecommendationSet? recommendations;
  final bool fromCache;

  bool get isEmpty => dashboard == null;
  bool get isSyncing => dashboard?.isSyncing ?? false;

  AnalyticsState copyWith({
    RecommendationSet? recommendations,
    bool? fromCache,
  }) =>
      AnalyticsState(
        dashboard: dashboard,
        tags: tags,
        rating: rating,
        weaknesses: weaknesses,
        recommendations: recommendations ?? this.recommendations,
        fromCache: fromCache ?? this.fromCache,
      );
}

/// Cached-first analytics access (mirrors the M2 contest repository). The cache
/// lives in the drift `Settings` KV table as JSON blobs, one key per section.
/// A failed network fetch never clears the cache — the offline guarantee.
class AnalyticsRepository {
  AnalyticsRepository(this._api, this._db);

  final AnalyticsApi _api;
  final AppDatabase _db;

  static const _kDashboard = 'analytics.dashboard';
  static const _kTags = 'analytics.tags';
  static const _kRating = 'analytics.rating';
  static const _kWeak = 'analytics.weaknesses';
  static const _kRecs = 'analytics.recommendations';

  /// Read the last-cached analytics, or null if nothing has been cached yet.
  Future<AnalyticsState?> readCache() async {
    final dashRaw = await _db.readSetting(_kDashboard);
    if (dashRaw == null) return null;
    return AnalyticsState(
      dashboard: DashboardData.fromJson(
          jsonDecode(dashRaw) as Map<String, dynamic>),
      tags: await _readList(_kTags, TagStat.fromJson),
      rating: await _readList(_kRating, RatingEntry.fromJson),
      weaknesses: await _readList(_kWeak, WeaknessSignal.fromJson),
      recommendations: await _readObj(_kRecs, RecommendationSet.fromJson),
      fromCache: true,
    );
  }

  /// Fetch every section in parallel, write each to the cache, and return the
  /// fresh state. **Throws** on network failure so the caller can fall back to
  /// cache.
  Future<AnalyticsState> fetchAndCache() async {
    final results = await Future.wait([
      _api.dashboard(),
      _api.tags(),
      _api.ratingHistory(),
      _api.weaknesses(),
      _api.recommendations(),
    ]);
    final dashboard = results[0] as DashboardData;
    final tags = results[1] as List<TagStat>;
    final rating = results[2] as List<RatingEntry>;
    final weaknesses = results[3] as List<WeaknessSignal>;
    final recs = results[4] as RecommendationSet?;

    await _db.writeSetting(_kDashboard, jsonEncode(dashboard.toJson()));
    await _db.writeSetting(_kTags, jsonEncode([for (final t in tags) t.toJson()]));
    await _db.writeSetting(_kRating, jsonEncode([for (final r in rating) r.toJson()]));
    await _db.writeSetting(_kWeak, jsonEncode([for (final w in weaknesses) w.toJson()]));
    await _db.writeSetting(_kRecs, recs == null ? 'null' : jsonEncode(recs.toJson()));

    return AnalyticsState(
      dashboard: dashboard,
      tags: tags,
      rating: rating,
      weaknesses: weaknesses,
      recommendations: recs,
      fromCache: false,
    );
  }

  /// Regenerate recommendations (no cooldown) and update just that cache slice.
  Future<RecommendationSet?> refreshRecommendations() async {
    final recs = await _api.refreshRecommendations();
    await _db.writeSetting(_kRecs, recs == null ? 'null' : jsonEncode(recs.toJson()));
    return recs;
  }

  Future<List<T>> _readList<T>(
      String key, T Function(Map<String, dynamic>) parse) async {
    final raw = await _db.readSetting(key);
    if (raw == null) return const [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list.map((e) => parse(e as Map<String, dynamic>)).toList();
  }

  Future<T?> _readObj<T>(
      String key, T Function(Map<String, dynamic>) parse) async {
    final raw = await _db.readSetting(key);
    if (raw == null || raw == 'null') return null;
    return parse(jsonDecode(raw) as Map<String, dynamic>);
  }
}
