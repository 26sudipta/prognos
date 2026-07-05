import 'package:dio/dio.dart';

import 'analytics_models.dart';

/// Typed wrapper over the `/analytics/*` endpoints. Uses the **authed** Dio
/// (Bearer + refresh-on-401). Each call parses into a model; the repository
/// re-encodes via `toJson` to cache the payload for offline use.
class AnalyticsApi {
  AnalyticsApi(this._dio);
  final Dio _dio;

  Future<DashboardData> dashboard() async {
    final res = await _dio.get<Map<String, dynamic>>('/analytics/dashboard');
    return DashboardData.fromJson(res.data ?? const {});
  }

  Future<List<TagStat>> tags() async {
    final res = await _dio.get<List<dynamic>>('/analytics/tags');
    return (res.data ?? const [])
        .map((e) => TagStat.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<RatingEntry>> ratingHistory() async {
    final res = await _dio.get<List<dynamic>>('/analytics/rating-history');
    return (res.data ?? const [])
        .map((e) => RatingEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<WeaknessSignal>> weaknesses() async {
    final res = await _dio.get<List<dynamic>>('/analytics/weaknesses');
    return (res.data ?? const [])
        .map((e) => WeaknessSignal.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RecommendationSet?> recommendations() async {
    final res = await _dio.get('/analytics/recommendations');
    final data = res.data;
    if (data == null) return null;
    return RecommendationSet.fromJson(data as Map<String, dynamic>);
  }

  Future<RecommendationSet?> refreshRecommendations() async {
    final res = await _dio.post('/analytics/recommendations/refresh');
    final data = res.data;
    if (data == null) return null;
    return RecommendationSet.fromJson(data as Map<String, dynamic>);
  }
}
