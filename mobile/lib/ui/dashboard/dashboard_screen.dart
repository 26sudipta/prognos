import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/analytics/analytics_providers.dart';
import '../../core/analytics/analytics_repository.dart';
import '../../theme/app_colors.dart';
import '../handles/handle_verify_screen.dart';
import '../widgets/skeleton.dart';
import 'widgets/activity_heatmap.dart';
import 'widgets/focus_areas.dart';
import 'widgets/rating_chart.dart';
import 'widgets/recommendations.dart';
import 'widgets/stat_strip.dart';
import 'widgets/tag_stats.dart';

/// Dashboard tab (M4). Cached-first analytics with an Overview ⇄ Insights
/// toggle; polls while the backend is syncing; renders offline from cache.
class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(analyticsProvider);

    if (async.isLoading && async.value == null) {
      return const _LoadingSkeleton();
    }

    final state = async.value ?? const AnalyticsState();
    final dash = state.dashboard;

    if (dash != null && !dash.hasVerifiedHandle) {
      return const _NoHandleNudge();
    }

    return RefreshIndicator(
      color: AppColors.primary400,
      backgroundColor: AppColors.bgSurfaceRaised,
      onRefresh: () => ref.read(analyticsProvider.notifier).refresh(),
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
        children: [
          if (state.fromCache) const _OfflineNote(),
          if (state.isSyncing) const _SyncingNote(),
          const _ViewToggle(),
          const SizedBox(height: 16),
          ..._body(ref, state),
        ],
      ),
    );
  }

  List<Widget> _body(WidgetRef ref, AnalyticsState state) {
    final view = ref.watch(dashboardViewProvider);
    final dash = state.dashboard;
    if (dash == null) {
      return [const _EmptyCard(text: 'No analytics yet — pull to refresh.')];
    }
    if (view == DashboardView.overview) {
      return [
        StatStrip(data: dash, rating: state.rating),
        const SizedBox(height: 12),
        ActivityHeatmap(days: dash.heatmap),
        const SizedBox(height: 12),
        RatingChart(rating: state.rating),
      ];
    }
    return [
      Recommendations(set: state.recommendations),
      const SizedBox(height: 12),
      FocusAreas(signals: state.weaknesses),
      const SizedBox(height: 12),
      TagStats(tags: state.tags),
    ];
  }
}

class _ViewToggle extends ConsumerWidget {
  const _ViewToggle();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final view = ref.watch(dashboardViewProvider);
    return SegmentedButton<DashboardView>(
      style: ButtonStyle(
        backgroundColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected)
              ? AppColors.primary500
              : AppColors.bgSurface,
        ),
        foregroundColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected)
              ? Colors.white
              : AppColors.textSecondary,
        ),
      ),
      showSelectedIcon: false,
      segments: const [
        ButtonSegment(value: DashboardView.overview, label: Text('Overview')),
        ButtonSegment(value: DashboardView.insights, label: Text('Insights')),
      ],
      selected: {view},
      onSelectionChanged: (s) =>
          ref.read(dashboardViewProvider.notifier).set(s.first),
    );
  }
}

class _SyncingNote extends StatelessWidget {
  const _SyncingNote();
  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
        decoration: BoxDecoration(
          color: AppColors.primary500.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Row(
          children: [
            SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(
                  strokeWidth: 2, color: AppColors.primary400),
            ),
            SizedBox(width: 10),
            Text('Syncing your latest submissions…',
                style: TextStyle(color: AppColors.primary400, fontSize: 12.5)),
          ],
        ),
      );
}

class _OfflineNote extends StatelessWidget {
  const _OfflineNote();
  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
        decoration: BoxDecoration(
          color: AppColors.warning500.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Row(
          children: [
            Icon(Icons.cloud_off_rounded, size: 15, color: AppColors.warning400),
            SizedBox(width: 8),
            Text('Offline — showing saved analytics',
                style: TextStyle(color: AppColors.warning400, fontSize: 12.5)),
          ],
        ),
      );
}

class _NoHandleNudge extends ConsumerWidget {
  const _NoHandleNudge();

  Future<void> _verify(BuildContext context, WidgetRef ref) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const HandleVerifyScreen()),
    );
    // Returning from the wizard: re-pull analytics in case the handle is now
    // verified (the controller also invalidates on success).
    await ref.read(analyticsProvider.notifier).refresh();
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.link_rounded,
                  size: 48, color: AppColors.textDisabled),
              const SizedBox(height: 16),
              const Text(
                'Link your Codeforces handle',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 17,
                    fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              const Text(
                'Verify your handle to unlock your dashboard, streaks and '
                'recommendations.',
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: AppColors.textSecondary, fontSize: 13.5, height: 1.4),
              ),
              const SizedBox(height: 20),
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.primary500,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 28, vertical: 13),
                ),
                onPressed: () => _verify(context, ref),
                child: const Text('Verify handle',
                    style: TextStyle(fontWeight: FontWeight.w700)),
              ),
            ],
          ),
        ),
      );
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: AppColors.bgSurface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.borderSubtle),
        ),
        child: Center(
          child: Text(text,
              style: const TextStyle(
                  color: AppColors.textMuted, fontSize: 13)),
        ),
      );
}

class _LoadingSkeleton extends StatelessWidget {
  const _LoadingSkeleton();
  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
        children: const [
          Skeleton(height: 40, radius: 10),
          SizedBox(height: 16),
          Row(children: [
            Expanded(child: Skeleton(height: 80, radius: 14)),
            SizedBox(width: 12),
            Expanded(child: Skeleton(height: 80, radius: 14)),
          ]),
          SizedBox(height: 12),
          Skeleton(height: 160, radius: 14),
          SizedBox(height: 12),
          Skeleton(height: 200, radius: 14),
        ],
      );
}
