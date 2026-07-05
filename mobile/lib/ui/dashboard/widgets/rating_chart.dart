import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/analytics/analytics_models.dart';
import '../../../theme/app_colors.dart';

/// Codeforces rating over time — an `fl_chart` area chart. Y-axis clamped to
/// [min−50, max+50] (matches the web); touch a point for contest + delta.
class RatingChart extends StatelessWidget {
  const RatingChart({super.key, required this.rating});
  final List<RatingEntry> rating;

  @override
  Widget build(BuildContext context) {
    final sorted = [...rating]
      ..sort((a, b) => a.contestTime.compareTo(b.contestTime));

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
      decoration: BoxDecoration(
        color: AppColors.bgSurface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.borderSubtle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Rating',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 16),
          if (sorted.length < 2)
            const SizedBox(
              height: 120,
              child: Center(
                child: Text(
                  'Not enough rated contests yet',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 13),
                ),
              ),
            )
          else
            SizedBox(height: 180, child: _chart(sorted)),
        ],
      ),
    );
  }

  Widget _chart(List<RatingEntry> data) {
    final ratings = data.map((e) => e.newRating).toList();
    final minR = ratings.reduce((a, b) => a < b ? a : b) - 50;
    final maxR = ratings.reduce((a, b) => a > b ? a : b) + 50;
    final spots = [
      for (var i = 0; i < data.length; i++)
        FlSpot(i.toDouble(), data[i].newRating.toDouble()),
    ];

    return LineChart(
      LineChartData(
        minY: minR.toDouble(),
        maxY: maxR.toDouble(),
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (_) => FlLine(
            color: AppColors.borderSubtle.withValues(alpha: 0.5),
            strokeWidth: 1,
          ),
        ),
        titlesData: FlTitlesData(
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 34,
              getTitlesWidget: (v, meta) => Text(
                v.toInt().toString(),
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 10),
              ),
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipColor: (_) => AppColors.bgSurfaceOverlay,
            getTooltipItems: (spots) => spots.map((s) {
              final e = data[s.x.toInt()];
              final sign = e.delta >= 0 ? '+' : '';
              return LineTooltipItem(
                '${e.contestName}\n',
                const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 11,
                    fontWeight: FontWeight.w600),
                children: [
                  TextSpan(
                    text: '${e.newRating}  ($sign${e.delta})\n',
                    style: TextStyle(
                      color: e.delta >= 0
                          ? AppColors.success400
                          : AppColors.danger400,
                      fontSize: 11,
                    ),
                  ),
                  TextSpan(
                    text: DateFormat('MMM d, y').format(e.contestTime.toLocal()),
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 10),
                  ),
                ],
              );
            }).toList(),
          ),
        ),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            barWidth: 2,
            color: AppColors.primary400,
            dotData: FlDotData(
              show: data.length <= 30,
              getDotPainter: (spot, _, _, _) => FlDotCirclePainter(
                radius: 2.5,
                color: AppColors.primary400,
                strokeWidth: 0,
              ),
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  AppColors.primary500.withValues(alpha: 0.35),
                  AppColors.primary500.withValues(alpha: 0.0),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
