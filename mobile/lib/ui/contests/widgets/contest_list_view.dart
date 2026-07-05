import 'package:flutter/material.dart';

import '../../../core/contests/contest_format.dart';
import '../../../core/db/app_database.dart';
import '../../../theme/app_colors.dart';
import 'contest_card.dart';
import 'contest_detail_sheet.dart';

/// Urgency swim-lane list (LIVE / TODAY / THIS WEEK / NEXT WEEK / LATER),
/// mirroring the web Direction-B layout. Ended contests are omitted.
///
/// Uses a **lazy** [ListView.builder] over a pre-flattened row model, so only
/// on-screen cards are built — this bounds the number of live 1-second
/// countdown timers to roughly the viewport rather than the whole 30-day
/// window (perf: mobile plan R5).
class ContestListView extends StatelessWidget {
  const ContestListView({super.key, required this.contests});

  final List<Contest> contests;

  @override
  Widget build(BuildContext context) {
    final lanes = groupByUrgency(contests);
    if (lanes.isEmpty) return const _EmptyState();

    // Flatten lanes → [header, card, card, header, card, …] for the builder.
    final rows = <_Row>[];
    for (final lane in lanes) {
      rows.add(_HeaderRow(lane.lane));
      rows.addAll(lane.contests.map(_CardRow.new));
    }

    return ListView.builder(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      itemCount: rows.length,
      itemBuilder: (context, i) {
        final row = rows[i];
        return switch (row) {
          _HeaderRow(:final lane) => _LaneHeader(lane),
          _CardRow(:final contest) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: ContestCard(
                contest: contest,
                onTap: () => ContestDetailSheet.show(context, contest),
              ),
            ),
        };
      },
    );
  }
}

sealed class _Row {
  const _Row();
}

class _HeaderRow extends _Row {
  const _HeaderRow(this.lane);
  final UrgencyLane lane;
}

class _CardRow extends _Row {
  const _CardRow(this.contest);
  final Contest contest;
}

class _LaneHeader extends StatelessWidget {
  const _LaneHeader(this.lane);
  final UrgencyLane lane;

  @override
  Widget build(BuildContext context) {
    final live = lane == UrgencyLane.live;
    return Padding(
      padding: const EdgeInsets.only(top: 6, bottom: 10),
      child: Row(
        children: [
          if (live)
            Container(
              width: 7,
              height: 7,
              margin: const EdgeInsets.only(right: 8),
              decoration: const BoxDecoration(
                color: AppColors.success400,
                shape: BoxShape.circle,
              ),
            ),
          Text(
            lane.label.toUpperCase(),
            style: TextStyle(
              color: live ? AppColors.success400 : AppColors.textMuted,
              fontSize: 12,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.8,
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    // Wrapped in a scroll view so pull-to-refresh still works when empty.
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      children: const [
        SizedBox(height: 120),
        Icon(Icons.event_busy_rounded, size: 48, color: AppColors.textDisabled),
        SizedBox(height: 16),
        Center(
          child: Text(
            'No upcoming contests',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 15),
          ),
        ),
        SizedBox(height: 6),
        Center(
          child: Text(
            'Pull down to refresh',
            style: TextStyle(color: AppColors.textMuted, fontSize: 13),
          ),
        ),
      ],
    );
  }
}
