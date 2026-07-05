import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/analytics/analytics_models.dart';
import '../../../theme/app_colors.dart';

/// GitHub-style activity heatmap drawn on a [CustomPainter] (no chart dep).
/// 53 week-columns × 7 weekday-rows ending today, 5 intensity levels by total
/// submission count (0 / 1–2 / 3–5 / 6–9 / 10+), matching the web thresholds.
/// Tap a cell to show that day's totals in the header.
class ActivityHeatmap extends StatefulWidget {
  const ActivityHeatmap({super.key, required this.days});
  final List<HeatmapDay> days;

  @override
  State<ActivityHeatmap> createState() => _ActivityHeatmapState();
}

class _ActivityHeatmapState extends State<ActivityHeatmap> {
  static const _cols = 53;
  static const _rows = 7;
  static const _gap = 3.0;
  static const _cell = 14.0;

  String? _selectedKey;

  static String _key(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    final byDate = {for (final d in widget.days) d.date: d};

    final today = DateTime.now();
    final todayMidnight = DateTime(today.year, today.month, today.day);
    // Sunday of this week (Dart weekday: Mon=1..Sun=7 → Sun index 0).
    final sundayThisWeek =
        todayMidnight.subtract(Duration(days: todayMidnight.weekday % 7));
    final start = sundayThisWeek.subtract(const Duration(days: (_cols - 1) * 7));

    final selected = _selectedKey == null ? null : byDate[_selectedKey];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.bgSurface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.borderSubtle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Activity',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Text(
                selected == null
                    ? 'Last year'
                    : '${DateFormat('MMM d').format(DateTime.parse(selected.date))} · ${selected.solved} solved',
                style: const TextStyle(
                    color: AppColors.textSecondary, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Fixed cell size + horizontal scroll (GitHub-mobile style). `reverse`
          // starts the view at the most-recent weeks; scroll left for history.
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            reverse: true,
            physics: const BouncingScrollPhysics(),
            child: SizedBox(
              width: _cols * _cell + (_cols - 1) * _gap,
              height: _rows * _cell + (_rows - 1) * _gap,
              child: GestureDetector(
                onTapDown: (d) {
                  final col = (d.localPosition.dx / (_cell + _gap)).floor();
                  final row = (d.localPosition.dy / (_cell + _gap)).floor();
                  if (col < 0 || col >= _cols || row < 0 || row >= _rows) {
                    return;
                  }
                  final date = start.add(Duration(days: col * 7 + row));
                  if (date.isAfter(todayMidnight)) return;
                  setState(() => _selectedKey = _key(date));
                },
                child: CustomPaint(
                  painter: _HeatmapPainter(
                    start: start,
                    today: todayMidnight,
                    byDate: byDate,
                    cell: _cell,
                    gap: _gap,
                    selectedKey: _selectedKey,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          const _Legend(),
        ],
      ),
    );
  }
}

Color _levelColor(int count) {
  if (count <= 0) return AppColors.bgSurfaceRaised;
  if (count <= 2) return AppColors.primary500.withValues(alpha: 0.30);
  if (count <= 5) return AppColors.primary500.withValues(alpha: 0.50);
  if (count <= 9) return AppColors.primary500.withValues(alpha: 0.75);
  return AppColors.primary500;
}

class _HeatmapPainter extends CustomPainter {
  _HeatmapPainter({
    required this.start,
    required this.today,
    required this.byDate,
    required this.cell,
    required this.gap,
    required this.selectedKey,
  });

  final DateTime start;
  final DateTime today;
  final Map<String, HeatmapDay> byDate;
  final double cell;
  final double gap;
  final String? selectedKey;

  static String _key(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  @override
  void paint(Canvas canvas, Size size) {
    final radius = Radius.circular(cell * 0.25);
    for (var col = 0; col < 53; col++) {
      for (var row = 0; row < 7; row++) {
        final date = start.add(Duration(days: col * 7 + row));
        if (date.isAfter(today)) continue;
        final key = _key(date);
        final count = byDate[key]?.count ?? 0;
        final paint = Paint()..color = _levelColor(count);
        final rect = Rect.fromLTWH(
          col * (cell + gap),
          row * (cell + gap),
          cell,
          cell,
        );
        canvas.drawRRect(RRect.fromRectAndRadius(rect, radius), paint);
        if (key == selectedKey) {
          canvas.drawRRect(
            RRect.fromRectAndRadius(rect, radius),
            Paint()
              ..style = PaintingStyle.stroke
              ..strokeWidth = 1.5
              ..color = AppColors.textPrimary,
          );
        }
      }
    }
  }

  @override
  bool shouldRepaint(_HeatmapPainter old) =>
      old.selectedKey != selectedKey ||
      old.cell != cell ||
      old.byDate != byDate;
}

class _Legend extends StatelessWidget {
  const _Legend();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        const Text('Less',
            style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
        const SizedBox(width: 6),
        for (final c in [0, 1, 3, 6, 10])
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 1.5),
            child: Container(
              width: 11,
              height: 11,
              decoration: BoxDecoration(
                color: _levelColor(c),
                borderRadius: BorderRadius.circular(3),
              ),
            ),
          ),
        const SizedBox(width: 6),
        const Text('More',
            style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
      ],
    );
  }
}
