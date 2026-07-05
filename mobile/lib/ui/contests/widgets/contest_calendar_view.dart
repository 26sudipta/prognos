import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/contests/contest_format.dart';
import '../../../core/contests/contests_providers.dart';
import '../../../core/db/app_database.dart';
import '../../../theme/app_colors.dart';
import 'contest_detail_sheet.dart';
import 'platform_badge.dart';

/// Week calendar: 7 vertical day columns (Mon–Sun, local TZ) with the day's
/// contests as tappable pills. Prev/next navigate weeks via [calendarWeekProvider].
class ContestCalendarView extends ConsumerWidget {
  const ContestCalendarView({super.key, required this.contests});

  final List<Contest> contests;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final weekOffset = ref.watch(calendarWeekProvider);
    final days = localWeekDays(weekOffset);
    final todayKey = _key(DateTime.now());

    return Column(
      children: [
        _WeekHeader(
          days: days,
          weekOffset: weekOffset,
          onPrev: () =>
              ref.read(calendarWeekProvider.notifier).state = weekOffset - 1,
          onNext: () =>
              ref.read(calendarWeekProvider.notifier).state = weekOffset + 1,
          onToday: () => ref.read(calendarWeekProvider.notifier).state = 0,
        ),
        Expanded(
          child: ListView.builder(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            itemCount: days.length,
            itemBuilder: (context, i) {
              final day = days[i];
              final dayContests = contestsOnLocalDay(contests, day);
              return _DayRow(
                day: day,
                isToday: _key(day) == todayKey,
                contests: dayContests,
              );
            },
          ),
        ),
      ],
    );
  }

  static String _key(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}

class _WeekHeader extends StatelessWidget {
  const _WeekHeader({
    required this.days,
    required this.weekOffset,
    required this.onPrev,
    required this.onNext,
    required this.onToday,
  });

  final List<DateTime> days;
  final int weekOffset;
  final VoidCallback onPrev;
  final VoidCallback onNext;
  final VoidCallback onToday;

  @override
  Widget build(BuildContext context) {
    final first = days.first;
    final last = days.last;
    final range = first.month == last.month
        ? '${DateFormat('MMM d').format(first)} – ${DateFormat('d').format(last)}'
        : '${DateFormat('MMM d').format(first)} – ${DateFormat('MMM d').format(last)}';

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 4, 8, 4),
      child: Row(
        children: [
          IconButton(
            onPressed: onPrev,
            icon: const Icon(Icons.chevron_left_rounded),
            color: AppColors.textSecondary,
          ),
          Expanded(
            child: GestureDetector(
              onTap: onToday,
              child: Text(
                range,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: weekOffset == 0
                      ? AppColors.primary400
                      : AppColors.textPrimary,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
          IconButton(
            onPressed: onNext,
            icon: const Icon(Icons.chevron_right_rounded),
            color: AppColors.textSecondary,
          ),
        ],
      ),
    );
  }
}

class _DayRow extends StatelessWidget {
  const _DayRow({
    required this.day,
    required this.isToday,
    required this.contests,
  });

  final DateTime day;
  final bool isToday;
  final List<Contest> contests;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Day label column
          SizedBox(
            width: 48,
            child: Column(
              children: [
                Text(
                  DateFormat('EEE').format(day).toUpperCase(),
                  style: TextStyle(
                    color: isToday
                        ? AppColors.primary400
                        : AppColors.textMuted,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 2),
                Container(
                  width: 30,
                  height: 30,
                  alignment: Alignment.center,
                  decoration: isToday
                      ? const BoxDecoration(
                          color: AppColors.primary500,
                          shape: BoxShape.circle,
                        )
                      : null,
                  child: Text(
                    '${day.day}',
                    style: TextStyle(
                      color:
                          isToday ? Colors.white : AppColors.textSecondary,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: contests.isEmpty
                ? Container(
                    height: 30,
                    alignment: Alignment.centerLeft,
                    child: const Text(
                      '—',
                      style: TextStyle(
                          color: AppColors.textDisabled, fontSize: 13),
                    ),
                  )
                : Column(
                    children: [
                      for (final c in contests)
                        _CalendarPill(contest: c),
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}

class _CalendarPill extends StatelessWidget {
  const _CalendarPill({required this.contest});
  final Contest contest;

  @override
  Widget build(BuildContext context) {
    final color = platformColor(contest.platform);
    final live = isLive(contest);
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Material(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: () => ContestDetailSheet.show(context, contest),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: live
                  ? Border.all(color: AppColors.success400, width: 1)
                  : null,
            ),
            child: Row(
              children: [
                PlatformBadge(contest.platform),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    contest.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  formatLocalTimeOnly(contest.startTime),
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    fontFeatures: [FontFeature.tabularFigures()],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
