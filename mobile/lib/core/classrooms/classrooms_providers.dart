import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../contests/contests_providers.dart';
import '../network/dio_client.dart';
import 'classroom_models.dart';
import 'classrooms_api.dart';
import 'classrooms_repository.dart';

final classroomsApiProvider = Provider<ClassroomsApi>(
  (ref) => ClassroomsApi(ref.watch(dioProvider)),
);

final classroomsRepositoryProvider = Provider<ClassroomsRepository>(
  (ref) => ClassroomsRepository(
    ref.watch(classroomsApiProvider),
    ref.watch(appDatabaseProvider),
  ),
);

/// Result wrapper carrying the offline flag for the classroom list.
class ClassroomListState {
  const ClassroomListState(this.classrooms, {this.fromCache = false});
  final List<Classroom> classrooms;
  final bool fromCache;
}

/// Cached-first classroom list (mirrors M2/M4).
class ClassroomsListNotifier extends AsyncNotifier<ClassroomListState> {
  ClassroomsRepository get _repo => ref.read(classroomsRepositoryProvider);

  @override
  Future<ClassroomListState> build() async {
    final cached = await _repo.readCachedList();
    if (cached != null) {
      Future.microtask(_refreshInBackground);
      return ClassroomListState(cached);
    }
    try {
      return ClassroomListState(await _repo.fetchList());
    } catch (_) {
      return const ClassroomListState([], fromCache: true);
    }
  }

  Future<void> _refreshInBackground() async {
    try {
      state = AsyncData(ClassroomListState(await _repo.fetchList()));
    } catch (_) {
      final cur = state.value;
      if (cur != null) {
        state = AsyncData(ClassroomListState(cur.classrooms, fromCache: true));
      }
    }
  }

  Future<void> refresh() => _refreshInBackground();
}

final classroomsListProvider =
    AsyncNotifierProvider<ClassroomsListNotifier, ClassroomListState>(
  ClassroomsListNotifier.new,
);

/// One classroom's leaderboard. Network-first, falling back to the drift cache
/// when offline (so a previously-seen board still renders). Polling while a bulk
/// sync runs is driven by the tab widget (invalidating this provider).
final leaderboardProvider =
    FutureProvider.family<Leaderboard, String>((ref, id) async {
  final repo = ref.watch(classroomsRepositoryProvider);
  try {
    return await repo.fetchLeaderboard(id);
  } catch (e) {
    final cached = await repo.readCachedLeaderboard(id);
    if (cached != null) return cached;
    rethrow;
  }
});

/// Kick a server-side bulk sync, then refresh the board.
Future<void> syncClassroom(WidgetRef ref, String id) async {
  try {
    await ref.read(classroomsApiProvider).sync(id);
  } catch (_) {}
  ref.invalidate(leaderboardProvider(id));
}

// ─── Live (uncached) secondary data ─────────────────────────────────────────

/// One classroom (for role/name). Prefers the cached list, else fetches.
final classroomProvider =
    FutureProvider.family<Classroom, String>((ref, id) async {
  final list = ref.watch(classroomsListProvider).value?.classrooms ?? const [];
  for (final c in list) {
    if (c.id == id) return c;
  }
  return ref.watch(classroomsApiProvider).get(id);
});

final membersProvider =
    FutureProvider.family<List<Member>, String>((ref, id) async {
  return ref.watch(classroomsApiProvider).members(id);
});

final cohortProvider =
    FutureProvider.family<CohortAnalytics, String>((ref, id) async {
  return ref.watch(classroomsApiProvider).cohort(id);
});

final invitesProvider =
    FutureProvider.family<List<Invite>, String>((ref, id) async {
  return ref.watch(classroomsApiProvider).invites(id);
});
