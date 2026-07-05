import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/analytics/analytics_models.dart';
import '../../../core/analytics/analytics_providers.dart';
import '../../../theme/app_colors.dart';
import '../../../theme/cf_rating.dart';

/// Recommended problems with a Refresh action. Difficulty uses the CF colour
/// ladder; tapping a problem opens it in the browser. Null set = sync hasn't
/// produced recommendations yet.
class Recommendations extends ConsumerStatefulWidget {
  const Recommendations({super.key, required this.set});
  final RecommendationSet? set;

  @override
  ConsumerState<Recommendations> createState() => _RecommendationsState();
}

class _RecommendationsState extends ConsumerState<Recommendations> {
  bool _refreshing = false;

  Future<void> _refresh() async {
    setState(() => _refreshing = true);
    await ref.read(analyticsProvider.notifier).refreshRecommendations();
    if (mounted) setState(() => _refreshing = false);
  }

  Future<void> _open(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final recs = widget.set?.recommendations ?? const [];
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
            children: [
              const Expanded(
                child: Text('Recommended',
                    style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 15,
                        fontWeight: FontWeight.w700)),
              ),
              if (widget.set != null)
                TextButton.icon(
                  onPressed: _refreshing ? null : _refresh,
                  icon: _refreshing
                      ? const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: AppColors.primary400),
                        )
                      : const Icon(Icons.refresh_rounded, size: 16),
                  label: const Text('Refresh'),
                ),
            ],
          ),
          const SizedBox(height: 8),
          if (widget.set == null)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 16),
              child: Text(
                'Sync has not produced recommendations yet.',
                style: TextStyle(color: AppColors.textMuted, fontSize: 13),
              ),
            )
          else
            for (final r in recs) _RecTile(rec: r, onTap: () => _open(r.url)),
        ],
      ),
    );
  }
}

class _RecTile extends StatelessWidget {
  const _RecTile({required this.rec, required this.onTap});
  final Recommendation rec;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = CfRating.color(rec.difficulty);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 9),
        child: Row(
          children: [
            Container(
              width: 46,
              padding: const EdgeInsets.symmetric(vertical: 4),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                '${rec.difficulty}',
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: color, fontSize: 12, fontWeight: FontWeight.w700),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    rec.problemName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        color: AppColors.textPrimary, fontSize: 14),
                  ),
                  Text(
                    rec.tag,
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 11.5),
                  ),
                ],
              ),
            ),
            const Icon(Icons.open_in_new_rounded,
                size: 15, color: AppColors.textMuted),
          ],
        ),
      ),
    );
  }
}
