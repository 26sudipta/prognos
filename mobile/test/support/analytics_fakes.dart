import 'package:dio/dio.dart';
import 'package:prognos/core/analytics/analytics_api.dart';
import 'package:prognos/core/analytics/analytics_models.dart';

DashboardData emptyDashboard({bool hasHandle = false, bool syncing = false}) =>
    DashboardData(
      heatmap: const [],
      currentStreak: 0,
      longestStreak: 0,
      totalSolved: 0,
      cfRating: null,
      hasVerifiedHandle: hasHandle,
      isSyncing: syncing,
    );

/// Fake [AnalyticsApi] — returns canned data or throws (offline). No network.
class FakeAnalyticsApi extends AnalyticsApi {
  FakeAnalyticsApi({
    DashboardData? dashboard,
    this.tagsData = const [],
    this.ratingData = const [],
    this.weaknessData = const [],
    this.recsData,
    this.throwError = false,
  })  : dashboardData = dashboard ?? emptyDashboard(),
        super(Dio());

  final DashboardData dashboardData;
  final List<TagStat> tagsData;
  final List<RatingEntry> ratingData;
  final List<WeaknessSignal> weaknessData;
  final RecommendationSet? recsData;
  final bool throwError;

  DioException get _err => DioException(
        requestOptions: RequestOptions(path: '/analytics'),
        type: DioExceptionType.connectionError,
      );

  @override
  Future<DashboardData> dashboard() async {
    if (throwError) throw _err;
    return dashboardData;
  }

  @override
  Future<List<TagStat>> tags() async {
    if (throwError) throw _err;
    return tagsData;
  }

  @override
  Future<List<RatingEntry>> ratingHistory() async {
    if (throwError) throw _err;
    return ratingData;
  }

  @override
  Future<List<WeaknessSignal>> weaknesses() async {
    if (throwError) throw _err;
    return weaknessData;
  }

  @override
  Future<RecommendationSet?> recommendations() async {
    if (throwError) throw _err;
    return recsData;
  }

  @override
  Future<RecommendationSet?> refreshRecommendations() async => recsData;
}
