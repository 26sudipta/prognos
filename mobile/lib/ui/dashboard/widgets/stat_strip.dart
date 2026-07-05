import 'package:flutter/material.dart';

import '../../../core/analytics/analytics_models.dart';
import '../../../theme/app_colors.dart';
import '../../../theme/cf_rating.dart';

/// Four headline stats — current streak, total solved, CF rating (in the CF
/// colour ladder), and peak rating — in a 2×2 grid. Mirrors the web stat strip.
class StatStrip extends StatelessWidget {
  const StatStrip({super.key, required this.data, required this.rating});

  final DashboardData data;
  final List<RatingEntry> rating;

  int? get _peak => rating.isEmpty
      ? data.cfRating
      : rating.map((r) => r.newRating).reduce((a, b) => a > b ? a : b);

  @override
  Widget build(BuildContext context) {
    final ratingColor = CfRating.color(data.cfRating);
    final peak = _peak;
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.7,
      children: [
        _StatCard(
          label: 'Current Streak',
          value: '${data.currentStreak}',
          unit: data.currentStreak == 1 ? 'day' : 'days',
          accent: AppColors.warning400,
          icon: Icons.local_fire_department_rounded,
        ),
        _StatCard(
          label: 'Total Solved',
          value: '${data.totalSolved}',
          accent: AppColors.success400,
          icon: Icons.check_circle_rounded,
        ),
        _StatCard(
          label: 'CF Rating',
          value: data.cfRating?.toString() ?? '—',
          unit: CfRating.rank(data.cfRating),
          accent: ratingColor,
          valueColor: ratingColor,
        ),
        _StatCard(
          label: 'Peak Rating',
          value: peak?.toString() ?? '—',
          accent: CfRating.color(peak),
          valueColor: CfRating.color(peak),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.label,
    required this.value,
    this.unit,
    required this.accent,
    this.valueColor,
    this.icon,
  });

  final String label;
  final String value;
  final String? unit;
  final Color accent;
  final Color? valueColor;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.bgSurface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.borderSubtle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              if (icon != null) ...[
                Icon(icon, size: 15, color: accent),
                const SizedBox(width: 6),
              ],
              Expanded(
                child: Text(
                  label.toUpperCase(),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.6,
                  ),
                ),
              ),
            ],
          ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                value,
                style: TextStyle(
                  color: valueColor ?? AppColors.textPrimary,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  height: 1,
                  letterSpacing: -0.5,
                ),
              ),
              if (unit != null) ...[
                const SizedBox(width: 5),
                Flexible(
                  child: Text(
                    unit!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}
