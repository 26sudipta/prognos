import '../db/app_database.dart';
import 'contests_api.dart';

/// A snapshot handed to the UI: the contests to render plus how they were
/// obtained. [fromCacheOnly] is true when a network refresh failed (offline /
/// server down) and we are showing whatever was last cached — this is the
/// offline guarantee, not an error.
class ContestsResult {
  const ContestsResult(
    this.contests, {
    required this.isStale,
    required this.fromCacheOnly,
  });

  final List<Contest> contests;
  final bool isStale;
  final bool fromCacheOnly;

  ContestsResult copyWith({bool? fromCacheOnly, bool? isStale}) =>
      ContestsResult(
        contests,
        isStale: isStale ?? this.isStale,
        fromCacheOnly: fromCacheOnly ?? this.fromCacheOnly,
      );
}

/// Cached-first contest access.
///
/// The whole M2 exit criterion (airplane mode → list still renders) hinges on
/// one rule: **a failed network fetch must never propagate or clear the cache.**
/// [fetchAndReplace] throws on network error so callers can decide; [readCache]
/// and the notifier keep the last-known-good rows when it does.
class ContestsRepository {
  ContestsRepository(this._api, this._db);

  final ContestsApi _api;
  final AppDatabase _db;

  Future<List<Contest>> readCache() => _db.allContests();

  /// Hit the network, replace the cache on success, and return the fresh
  /// window. **Throws** on any network/parse failure — the caller is
  /// responsible for falling back to cache.
  Future<ContestsResult> fetchAndReplace() async {
    final fetched = await _api.fetchContests();
    await _db.replaceContests(fetched.contests);
    return ContestsResult(
      fetched.contests,
      isStale: fetched.isStale,
      fromCacheOnly: false,
    );
  }
}
