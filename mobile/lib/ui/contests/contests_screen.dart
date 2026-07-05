import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/contests/contest_format.dart';
import '../../core/contests/contests_providers.dart';
import '../../core/db/app_database.dart';
import '../../theme/app_colors.dart';
import '../widgets/skeleton.dart';
import 'widgets/contest_banner.dart';
import 'widgets/contest_calendar_view.dart';
import 'widgets/contest_list_view.dart';
import 'widgets/next_contest_hero.dart';
import 'widgets/platform_filter_chips.dart';

/// Contests tab (M2). Cached-first: renders the last-synced window instantly
/// from the local store, refreshes in the background, and works fully offline.
/// List (urgency lanes) ⇄ calendar (week grid); platform filter applied
/// client-side; pull-to-refresh re-fetches.
class ContestsScreen extends ConsumerWidget {
  const ContestsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(contestsProvider);
    final view = ref.watch(contestViewProvider);
    final filtered = ref.watch(filteredContestsProvider);

    // True first-ever visit (empty cache, network in flight) → shimmer.
    if (async.isLoading && async.value == null) {
      return const _LoadingSkeleton();
    }

    final result = async.value;
    final offline = result?.fromCacheOnly ?? false;
    final stale = result?.isStale ?? false;

    return Column(
      children: [
        ContestBanner(offline: offline, stale: stale),
        _Toolbar(view: view),
        PlatformFilterChips(),
        const SizedBox(height: 4),
        Expanded(
          child: RefreshIndicator(
            color: AppColors.primary400,
            backgroundColor: AppColors.bgSurfaceRaised,
            onRefresh: () => ref.read(contestsProvider.notifier).refresh(),
            child: view == ContestView.list
                ? _ListBody(contests: filtered)
                : ContestCalendarView(contests: filtered),
          ),
        ),
      ],
    );
  }
}

class _ListBody extends StatelessWidget {
  const _ListBody({required this.contests});
  final List<Contest> contests;

  @override
  Widget build(BuildContext context) {
    final hero = nextContest(contests);
    return Column(
      children: [
        if (hero != null) NextContestHero(contest: hero),
        Expanded(child: ContestListView(contests: contests)),
      ],
    );
  }
}

class _Toolbar extends ConsumerWidget {
  const _Toolbar({required this.view});
  final ContestView view;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          SegmentedButton<ContestView>(
            style: ButtonStyle(
              visualDensity: VisualDensity.compact,
              backgroundColor: WidgetStateProperty.resolveWith(
                (states) => states.contains(WidgetState.selected)
                    ? AppColors.primary500
                    : AppColors.bgSurface,
              ),
              foregroundColor: WidgetStateProperty.resolveWith(
                (states) => states.contains(WidgetState.selected)
                    ? Colors.white
                    : AppColors.textSecondary,
              ),
            ),
            showSelectedIcon: false,
            segments: const [
              ButtonSegment(
                value: ContestView.list,
                icon: Icon(Icons.view_agenda_outlined, size: 18),
                label: Text('List'),
              ),
              ButtonSegment(
                value: ContestView.calendar,
                icon: Icon(Icons.calendar_month_outlined, size: 18),
                label: Text('Week'),
              ),
            ],
            selected: {view},
            onSelectionChanged: (s) =>
                ref.read(contestViewProvider.notifier).state = s.first,
          ),
        ],
      ),
    );
  }
}

class _LoadingSkeleton extends StatelessWidget {
  const _LoadingSkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
      children: [
        const Skeleton(height: 120, radius: 16),
        const SizedBox(height: 20),
        const Skeleton(width: 90, height: 14),
        const SizedBox(height: 14),
        for (var i = 0; i < 5; i++) ...[
          const Skeleton(height: 92, radius: 12),
          const SizedBox(height: 10),
        ],
      ],
    );
  }
}
