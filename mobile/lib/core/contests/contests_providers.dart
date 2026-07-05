import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../db/app_database.dart';
import '../network/dio_client.dart';
import 'contest_format.dart';
import 'contests_api.dart';
import 'contests_repository.dart';

/// App-wide drift database (one open connection for the process lifetime).
final appDatabaseProvider = Provider<AppDatabase>((ref) {
  final db = AppDatabase();
  ref.onDispose(db.close);
  return db;
});

final contestsApiProvider = Provider<ContestsApi>(
  (ref) => ContestsApi(ref.watch(dioProvider)),
);

final contestsRepositoryProvider = Provider<ContestsRepository>(
  (ref) => ContestsRepository(
    ref.watch(contestsApiProvider),
    ref.watch(appDatabaseProvider),
  ),
);

/// Cached-first contest state.
///
/// - **Repeat visit** (cache present): returns cached rows immediately (no
///   shimmer), then refreshes in the background and diff-updates.
/// - **First-ever visit** (empty cache): awaits the network (shimmer shows);
///   on failure returns an empty result rather than an error screen.
/// - **Pull-to-refresh** ([refresh]): re-fetches without dropping the current
///   view; on failure keeps the shown data and flags `fromCacheOnly`.
class ContestsNotifier extends AsyncNotifier<ContestsResult> {
  ContestsRepository get _repo => ref.read(contestsRepositoryProvider);

  @override
  Future<ContestsResult> build() async {
    final cached = await _repo.readCache();
    if (cached.isNotEmpty) {
      // Show cache now; refresh in the background.
      Future.microtask(_backgroundRefresh);
      return ContestsResult(cached, isStale: false, fromCacheOnly: false);
    }
    // First-ever load: the network is the only source. Never surface an error
    // here — degrade to an empty window so the screen shows its empty state.
    try {
      return await _repo.fetchAndReplace();
    } catch (_) {
      return const ContestsResult([], isStale: false, fromCacheOnly: true);
    }
  }

  Future<void> _backgroundRefresh() async {
    try {
      final fresh = await _repo.fetchAndReplace();
      state = AsyncData(fresh);
    } catch (_) {
      // Offline / server down: keep the cached emission untouched.
      final cur = state.value;
      if (cur != null) state = AsyncData(cur.copyWith(fromCacheOnly: true));
    }
  }

  /// Pull-to-refresh. Awaited by the UI's [RefreshIndicator].
  Future<void> refresh() async {
    try {
      state = AsyncData(await _repo.fetchAndReplace());
    } catch (_) {
      final cur = state.value;
      state = AsyncData(
        (cur ?? const ContestsResult([], isStale: false, fromCacheOnly: true))
            .copyWith(fromCacheOnly: true),
      );
    }
  }
}

final contestsProvider =
    AsyncNotifierProvider<ContestsNotifier, ContestsResult>(
  ContestsNotifier.new,
);

// ─── View state (list ⇄ calendar, platform filter, calendar week) ───────────

enum ContestView { list, calendar }

final contestViewProvider = StateProvider<ContestView>((_) => ContestView.list);

/// Selected platform filter (empty = all). Applied **client-side** to the
/// cached window so filtering works offline and needs no re-fetch.
final platformFilterProvider = StateProvider<Set<String>>((_) => <String>{});

/// Calendar week offset (0 = current week).
final calendarWeekProvider = StateProvider<int>((_) => 0);

/// Contests after applying the active platform filter, sorted by start time.
final filteredContestsProvider = Provider<List<Contest>>((ref) {
  final all = ref.watch(contestsProvider).value?.contests ?? const [];
  final filter = ref.watch(platformFilterProvider);
  final list = filter.isEmpty
      ? [...all]
      : all.where((c) => filter.contains(c.platform)).toList();
  list.sort((a, b) => a.startTime.compareTo(b.startTime));
  return list;
});

/// Distinct platforms present in the cached window (for filter chips).
final availablePlatformsProvider = Provider<List<String>>((ref) {
  final all = ref.watch(contestsProvider).value?.contests ?? const [];
  return distinctPlatforms(all);
});
