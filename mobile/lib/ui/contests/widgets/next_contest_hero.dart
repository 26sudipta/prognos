import 'package:flutter/material.dart';

import '../../../core/contests/contest_format.dart';
import '../../../core/db/app_database.dart';
import '../../../theme/app_colors.dart';
import 'contest_countdown.dart';
import 'contest_detail_sheet.dart';
import 'platform_badge.dart';

/// Featured next/live contest — a platform-tinted panel with a large countdown.
/// Null-safe: renders nothing when there is no upcoming or live contest.
class NextContestHero extends StatelessWidget {
  const NextContestHero({super.key, required this.contest});

  final Contest? contest;

  @override
  Widget build(BuildContext context) {
    final c = contest;
    if (c == null) return const SizedBox.shrink();

    final color = platformColor(c.platform);
    final live = isLive(c);

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => ContestDetailSheet.show(context, c),
          child: Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  color.withValues(alpha: live ? 0.22 : 0.16),
                  AppColors.bgSurface,
                ],
              ),
              border: Border.all(
                color: live
                    ? AppColors.success400.withValues(alpha: 0.6)
                    : color.withValues(alpha: 0.35),
                width: 1,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      live ? 'HAPPENING NOW' : 'NEXT UP',
                      style: TextStyle(
                        color: live
                            ? AppColors.success400
                            : AppColors.textSecondary,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1,
                      ),
                    ),
                    const Spacer(),
                    PlatformBadge(c.platform),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  c.name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 19,
                    fontWeight: FontWeight.w700,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    const Icon(Icons.schedule_rounded,
                        size: 14, color: AppColors.textMuted),
                    const SizedBox(width: 5),
                    Text(
                      formatLocalDateTimeShort(c.startTime),
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                ContestCountdown(contest: c, large: true),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
