// Analytics domain models — a 1:1 port of the web frontend/app/_lib/analytics.ts
// shapes. Each type round-trips (fromJson/toJson) so the repository can cache the
// exact server payload in drift for offline, cached-first rendering.

int? _asIntOrNull(dynamic v) => v == null ? null : (v as num).toInt();

class HeatmapDay {
  const HeatmapDay({required this.date, required this.count, required this.solved});
  final String date; // YYYY-MM-DD
  final int count; // total submissions (drives intensity)
  final int solved; // accepted (tooltip)

  factory HeatmapDay.fromJson(Map<String, dynamic> j) => HeatmapDay(
        date: j['date'] as String,
        count: (j['count'] as num).toInt(),
        solved: (j['solved'] as num?)?.toInt() ?? 0,
      );
  Map<String, dynamic> toJson() =>
      {'date': date, 'count': count, 'solved': solved};
}

class DashboardData {
  const DashboardData({
    required this.heatmap,
    required this.currentStreak,
    required this.longestStreak,
    required this.totalSolved,
    required this.cfRating,
    required this.hasVerifiedHandle,
    required this.isSyncing,
  });

  final List<HeatmapDay> heatmap;
  final int currentStreak;
  final int longestStreak;
  final int totalSolved;
  final int? cfRating;
  final bool hasVerifiedHandle;
  final bool isSyncing;

  factory DashboardData.fromJson(Map<String, dynamic> j) => DashboardData(
        heatmap: (j['heatmap'] as List<dynamic>? ?? const [])
            .map((e) => HeatmapDay.fromJson(e as Map<String, dynamic>))
            .toList(),
        currentStreak: (j['current_streak'] as num?)?.toInt() ?? 0,
        longestStreak: (j['longest_streak'] as num?)?.toInt() ?? 0,
        totalSolved: (j['total_solved'] as num?)?.toInt() ?? 0,
        cfRating: _asIntOrNull(j['cf_rating']),
        hasVerifiedHandle: j['has_verified_handle'] == true,
        isSyncing: j['is_syncing'] == true,
      );

  Map<String, dynamic> toJson() => {
        'heatmap': [for (final d in heatmap) d.toJson()],
        'current_streak': currentStreak,
        'longest_streak': longestStreak,
        'total_solved': totalSolved,
        'cf_rating': cfRating,
        'has_verified_handle': hasVerifiedHandle,
        'is_syncing': isSyncing,
      };
}

class TagStat {
  const TagStat({
    required this.tag,
    required this.solvedCount,
    required this.attemptCount,
    required this.acceptanceRate,
  });
  final String tag;
  final int solvedCount;
  final int attemptCount;
  final double acceptanceRate;

  factory TagStat.fromJson(Map<String, dynamic> j) => TagStat(
        tag: j['tag'] as String,
        solvedCount: (j['solved_count'] as num).toInt(),
        attemptCount: (j['attempt_count'] as num).toInt(),
        acceptanceRate: (j['acceptance_rate'] as num).toDouble(),
      );
  Map<String, dynamic> toJson() => {
        'tag': tag,
        'solved_count': solvedCount,
        'attempt_count': attemptCount,
        'acceptance_rate': acceptanceRate,
      };
}

class RatingEntry {
  const RatingEntry({
    required this.contestName,
    required this.oldRating,
    required this.newRating,
    required this.delta,
    required this.rank,
    required this.contestTime,
  });
  final String contestName;
  final int oldRating;
  final int newRating;
  final int delta;
  final int rank;
  final DateTime contestTime; // UTC

  factory RatingEntry.fromJson(Map<String, dynamic> j) => RatingEntry(
        contestName: j['contest_name'] as String,
        oldRating: (j['old_rating'] as num).toInt(),
        newRating: (j['new_rating'] as num).toInt(),
        delta: (j['delta'] as num).toInt(),
        rank: (j['rank'] as num).toInt(),
        contestTime: DateTime.parse(j['contest_time'] as String).toUtc(),
      );
  Map<String, dynamic> toJson() => {
        'contest_name': contestName,
        'old_rating': oldRating,
        'new_rating': newRating,
        'delta': delta,
        'rank': rank,
        'contest_time': contestTime.toIso8601String(),
      };
}

class WeaknessSignal {
  const WeaknessSignal({
    required this.tag,
    required this.signalType,
    required this.score,
    required this.reason,
  });
  final String tag;
  final String signalType; // low_success | neglected | under_practiced
  final double score;
  final String reason;

  factory WeaknessSignal.fromJson(Map<String, dynamic> j) => WeaknessSignal(
        tag: j['tag'] as String,
        signalType: j['signal_type'] as String,
        score: (j['score'] as num).toDouble(),
        reason: j['reason'] as String,
      );
  Map<String, dynamic> toJson() => {
        'tag': tag,
        'signal_type': signalType,
        'score': score,
        'reason': reason,
      };
}

class Recommendation {
  const Recommendation({
    required this.problemName,
    required this.tag,
    required this.difficulty,
    required this.url,
    required this.reason,
    required this.position,
  });
  final String problemName;
  final String tag;
  final int difficulty;
  final String url;
  final String reason;
  final int position;

  factory Recommendation.fromJson(Map<String, dynamic> j) => Recommendation(
        problemName: j['problem_name'] as String,
        tag: j['tag'] as String,
        difficulty: (j['difficulty'] as num).toInt(),
        url: j['url'] as String,
        reason: j['reason'] as String,
        position: (j['position'] as num).toInt(),
      );
  Map<String, dynamic> toJson() => {
        'problem_name': problemName,
        'tag': tag,
        'difficulty': difficulty,
        'url': url,
        'reason': reason,
        'position': position,
      };
}

class RecommendationSet {
  const RecommendationSet({required this.recommendations});
  final List<Recommendation> recommendations;

  factory RecommendationSet.fromJson(Map<String, dynamic> j) => RecommendationSet(
        recommendations: (j['recommendations'] as List<dynamic>? ?? const [])
            .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
  Map<String, dynamic> toJson() =>
      {'recommendations': [for (final r in recommendations) r.toJson()]};
}
