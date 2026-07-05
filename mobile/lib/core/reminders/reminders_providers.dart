import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../contests/contests_providers.dart';
import '../db/app_database.dart';
import 'reminder_scheduler.dart';
import 'reminders_repository.dart';

/// Process-wide scheduler (owns the plugin + timezone state). Initialized once
/// in the app bootstrap (post-first-frame).
final reminderSchedulerProvider =
    Provider<ReminderScheduler>((_) => ReminderScheduler());

final remindersRepositoryProvider = Provider<RemindersRepository>(
  (ref) => RemindersRepository(
    ref.watch(appDatabaseProvider),
    ref.watch(reminderSchedulerProvider),
  ),
);

/// Snapshot of all reminder-related state for the UI.
class RemindersState {
  const RemindersState({
    required this.starredIds,
    required this.platformRules,
    required this.leadMinutes,
    required this.upcoming,
  });

  final Set<String> starredIds;
  final Map<String, bool> platformRules; // platform → enabled
  final List<int> leadMinutes;
  final List<ScheduledReminder> upcoming;

  bool isStarred(String contestId) => starredIds.contains(contestId);
}

class RemindersController extends AsyncNotifier<RemindersState> {
  RemindersRepository get _repo => ref.read(remindersRepositoryProvider);

  @override
  Future<RemindersState> build() => _load();

  Future<RemindersState> _load() async {
    return RemindersState(
      starredIds: await _repo.starredIds(),
      platformRules: {
        for (final r in await _repo.platformRules()) r.platform: r.enabled,
      },
      leadMinutes: await _repo.leadMinutes(),
      upcoming: await _repo.upcomingReminders(),
    );
  }

  Future<void> toggleStar(String contestId) async {
    final isStarred = state.value?.isStarred(contestId) ?? false;
    await _repo.setStar(contestId, !isStarred);
    state = AsyncData(await _load());
  }

  Future<void> setPlatformRule(String platform, bool enabled) async {
    await _repo.setPlatformRule(platform, enabled);
    state = AsyncData(await _load());
  }

  Future<void> setLeadMinutes(List<int> minutes) async {
    await _repo.setLeadMinutes(minutes);
    state = AsyncData(await _load());
  }

  /// Re-run reconcile against current state (app foreground, after a cache
  /// refresh). Cheap and idempotent.
  Future<void> refresh() async {
    await _repo.reconcile();
    state = AsyncData(await _load());
  }
}

final remindersControllerProvider =
    AsyncNotifierProvider<RemindersController, RemindersState>(
  RemindersController.new,
);

/// Whether a specific contest is starred — a targeted `select` so a bell only
/// rebuilds when *its* contest's star changes.
final isStarredProvider = Provider.family<bool, String>((ref, contestId) {
  return ref.watch(
    remindersControllerProvider
        .select((s) => s.value?.isStarred(contestId) ?? false),
  );
});
