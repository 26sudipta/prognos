import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/analytics/analytics_models.dart';

void main() {
  test('DashboardData round-trips through JSON', () {
    final original = DashboardData.fromJson(const {
      'heatmap': [
        {'date': '2026-06-25', 'count': 5, 'solved': 3},
      ],
      'current_streak': 7,
      'longest_streak': 23,
      'total_solved': 412,
      'cf_rating': 1724,
      'has_verified_handle': true,
      'is_syncing': false,
    });

    final round = DashboardData.fromJson(original.toJson());
    expect(round.currentStreak, 7);
    expect(round.totalSolved, 412);
    expect(round.cfRating, 1724);
    expect(round.hasVerifiedHandle, isTrue);
    expect(round.heatmap.single.count, 5);
    expect(round.heatmap.single.solved, 3);
  });

  test('handles null cf_rating and missing is_syncing', () {
    final d = DashboardData.fromJson(const {
      'heatmap': [],
      'current_streak': 0,
      'longest_streak': 0,
      'total_solved': 0,
      'cf_rating': null,
      'has_verified_handle': false,
    });
    expect(d.cfRating, isNull);
    expect(d.isSyncing, isFalse);
  });

  test('RatingEntry parses UTC time and survives round-trip', () {
    final e = RatingEntry.fromJson(const {
      'cf_contest_id': 1,
      'contest_name': 'Round 950',
      'old_rating': 1500,
      'new_rating': 1560,
      'delta': 60,
      'rank': 320,
      'contest_time': '2026-06-01T14:00:00+00:00',
    });
    expect(e.contestTime.isUtc, isTrue);
    final round = RatingEntry.fromJson(e.toJson());
    expect(round.newRating, 1560);
    expect(round.delta, 60);
    expect(round.contestTime, e.contestTime);
  });

  test('RecommendationSet round-trips its problem list', () {
    final s = RecommendationSet.fromJson(const {
      'recommendations': [
        {
          'problem_name': 'Two Sum',
          'tag': 'dp',
          'difficulty': 1400,
          'url': 'https://cf/1',
          'reason': 'weak dp',
          'position': 1,
        },
      ],
    });
    final round = RecommendationSet.fromJson(s.toJson());
    expect(round.recommendations.single.problemName, 'Two Sum');
    expect(round.recommendations.single.difficulty, 1400);
  });
}
