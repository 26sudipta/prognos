import 'package:flutter/material.dart';

import '../../../core/analytics/analytics_models.dart';
import '../../../theme/app_colors.dart';

/// Top tags by problems solved, as horizontal bars relative to the max, with a
/// per-tag solved-rate label. Mirrors the web tag-stats list (top 15).
class TagStats extends StatelessWidget {
  const TagStats({super.key, required this.tags});
  final List<TagStat> tags;

  @override
  Widget build(BuildContext context) {
    final sorted = [...tags]
      ..sort((a, b) => b.solvedCount.compareTo(a.solvedCount));
    final top = sorted.take(15).toList();
    if (top.isEmpty) {
      return const _EmptyCard(text: 'No tag data yet');
    }
    final maxSolved = top.first.solvedCount.clamp(1, 1 << 30);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: _cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _CardTitle('Tags'),
          const SizedBox(height: 12),
          for (final t in top) _TagRow(tag: t, maxSolved: maxSolved),
        ],
      ),
    );
  }
}

class _TagRow extends StatelessWidget {
  const _TagRow({required this.tag, required this.maxSolved});
  final TagStat tag;
  final int maxSolved;

  @override
  Widget build(BuildContext context) {
    final frac = (tag.solvedCount / maxSolved).clamp(0.0, 1.0);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  tag.tag,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      color: AppColors.textPrimary, fontSize: 13),
                ),
              ),
              Text(
                '${tag.solvedCount}',
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Text(
                '  ·  ${(tag.acceptanceRate * 100).round()}% solved',
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 11.5),
              ),
            ],
          ),
          const SizedBox(height: 5),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: frac,
              minHeight: 6,
              backgroundColor: AppColors.bgSurfaceRaised,
              valueColor:
                  const AlwaysStoppedAnimation(AppColors.primary400),
            ),
          ),
        ],
      ),
    );
  }
}

const _cardDecoration = BoxDecoration(
  color: AppColors.bgSurface,
  borderRadius: BorderRadius.all(Radius.circular(14)),
  border: Border.fromBorderSide(BorderSide(color: AppColors.borderSubtle)),
);

class _CardTitle extends StatelessWidget {
  const _CardTitle(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Text(
        text,
        style: const TextStyle(
          color: AppColors.textPrimary,
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      );
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(24),
        decoration: _cardDecoration,
        child: Center(
          child: Text(text,
              style: const TextStyle(
                  color: AppColors.textMuted, fontSize: 13)),
        ),
      );
}
