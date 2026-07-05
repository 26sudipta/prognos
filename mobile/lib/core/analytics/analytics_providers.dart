import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../contests/contests_providers.dart';
import '../network/dio_client.dart';
import 'analytics_api.dart';
import 'analytics_repository.dart';

final analyticsApiProvider = Provider<AnalyticsApi>(
  (ref) => AnalyticsApi(ref.watch(dioProvider)),
);

final analyticsRepositoryProvider = Provider<AnalyticsRepository>(
  (ref) => AnalyticsRepository(
    ref.watch(analyticsApiProvider),
    ref.watch(appDatabaseProvider),
  ),
);

/// Cached-first analytics state with sync polling.
///
/// - Repeat visit: render cache instantly, refresh in the background.
/// - First-ever: await the network (shimmer); on failure show an empty state.
/// - While the backend reports `is_syncing`, poll every 5s (matching the web)
///   until the first sync completes, then stop.
class AnalyticsNotifier extends AsyncNotifier<AnalyticsState> {
  Timer? _poll;
  AnalyticsRepository get _repo => ref.read(analyticsRepositoryProvider);

  @override
  Future<AnalyticsState> build() async {
    ref.onDispose(() => _poll?.cancel());
    final cached = await _repo.readCache();
    if (cached != null) {
      Future.microtask(_refreshInBackground);
      _setPolling(cached.isSyncing);
      return cached;
    }
    try {
      final fresh = await _repo.fetchAndCache();
      _setPolling(fresh.isSyncing);
      return fresh;
    } catch (_) {
      return const AnalyticsState(fromCache: true);
    }
  }

  Future<void> _refreshInBackground() async {
    try {
      final fresh = await _repo.fetchAndCache();
      state = AsyncData(fresh);
      _setPolling(fresh.isSyncing);
    } catch (_) {
      final cur = state.value;
      if (cur != null) state = AsyncData(cur.copyWith(fromCache: true));
    }
  }

  /// Pull-to-refresh.
  Future<void> refresh() => _refreshInBackground();

  Future<void> refreshRecommendations() async {
    try {
      final recs = await _repo.refreshRecommendations();
      final cur = state.value;
      if (cur != null) {
        state = AsyncData(cur.copyWith(recommendations: recs));
      }
    } catch (_) {
      // keep existing recommendations
    }
  }

  void _setPolling(bool syncing) {
    _poll?.cancel();
    if (syncing) {
      _poll = Timer.periodic(
        const Duration(seconds: 5),
        (_) => _refreshInBackground(),
      );
    }
  }
}

final analyticsProvider =
    AsyncNotifierProvider<AnalyticsNotifier, AnalyticsState>(
  AnalyticsNotifier.new,
);

/// Dashboard sub-view toggle.
enum DashboardView { overview, insights }

final dashboardViewProvider = NotifierProvider<DashboardViewNotifier, DashboardView>(
  DashboardViewNotifier.new,
);

class DashboardViewNotifier extends Notifier<DashboardView> {
  @override
  DashboardView build() => DashboardView.overview;
  void set(DashboardView v) => state = v;
}
