import 'package:flutter/material.dart';

import '../../../core/contests/contest_format.dart';
import '../../../core/db/app_database.dart';
import '../../../theme/app_colors.dart';
import '../../reminders/reminder_bell.dart';
import 'contest_countdown.dart';
import 'platform_badge.dart';

/// One contest row. Left border + subtle tint encode status (live = emerald,
/// <1h = red, else platform color), matching the web card's four-level status
/// language. Tapping opens the detail sheet via [onTap].
class ContestCard extends StatelessWidget {
  const ContestCard({super.key, required this.contest, required this.onTap});

  final Contest contest;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now().toUtc();
    final live = isLive(contest, now);
    final soon = !live &&
        contest.startTime.isAfter(now) &&
        contest.startTime.difference(now).inHours < 1;

    final accent = live
        ? AppColors.success400
        : soon
            ? AppColors.danger400
            : platformColor(contest.platform);

    return Material(
      color: AppColors.bgSurface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border(left: BorderSide(color: accent, width: 3)),
          ),
          padding: const EdgeInsets.fromLTRB(14, 12, 12, 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        PlatformBadge(contest.platform),
                        const SizedBox(width: 8),
                        Text(
                          platformDisplayName(contest.platform),
                          style: const TextStyle(
                            color: AppColors.textMuted,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      contest.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        height: 1.25,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.schedule_rounded,
                            size: 13, color: AppColors.textMuted),
                        const SizedBox(width: 4),
                        Flexible(
                          child: Text(
                            formatLocalDateShort(contest.startTime),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 12.5,
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Icon(Icons.hourglass_empty_rounded,
                            size: 13, color: AppColors.textMuted),
                        const SizedBox(width: 4),
                        Text(
                          formatDuration(contest.durationSeconds),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12.5,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 6),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  ReminderBell(contestId: contest.id, size: 20),
                  const SizedBox(height: 2),
                  ContestCountdown(contest: contest),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
