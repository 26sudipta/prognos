import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

part 'app_database.g.dart';

/// Local cache of the contest window last fetched from `GET /contests`.
///
/// One row per contest (PK = server UUID). Timestamps are stored as UTC
/// instants; presentation converts to local time. `cachedAt` records when the
/// row was written so the UI can reason about cache freshness offline.
class Contests extends Table {
  TextColumn get id => text()();
  IntColumn get clistId => integer()();
  TextColumn get platform => text()();
  TextColumn get name => text()();
  DateTimeColumn get startTime => dateTime()();
  DateTimeColumn get endTime => dateTime()();
  IntColumn get durationSeconds => integer()();
  TextColumn get url => text()();
  DateTimeColumn get lastSyncedAt => dateTime()();
  DateTimeColumn get cachedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

/// Per-contest reminder toggle ("bell"). Presence = starred.
class StarredContests extends Table {
  TextColumn get contestId => text()();
  @override
  Set<Column> get primaryKey => {contestId};
}

/// Per-platform auto-reminder rule. A row with `enabled=true` means "remind me
/// for every contest on this platform" (M3 v1 granularity: per-platform only).
class PlatformRules extends Table {
  TextColumn get platform => text()();
  BoolColumn get enabled => boolean().withDefault(const Constant(false))();
  @override
  Set<Column> get primaryKey => {platform};
}

/// Ledger of intended reminders — the reconcile *intent* and the source for the
/// settings "upcoming reminders" list. The OS pending set is the truth for what
/// is actually scheduled; this table is reconciled toward it.
class ScheduledReminders extends Table {
  IntColumn get notifId => integer()(); // deterministic, 31-bit (reminder_ids)
  TextColumn get contestId => text()();
  IntColumn get leadMinutes => integer()();
  DateTimeColumn get fireAt => dateTime()();
  @override
  Set<Column> get primaryKey => {notifId};
}

/// Tiny key-value store for app settings (e.g. reminder lead times as CSV).
class Settings extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();
  @override
  Set<Column> get primaryKey => {key};
}

@DriftDatabase(
  tables: [Contests, StarredContests, PlatformRules, ScheduledReminders, Settings],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase([QueryExecutor? executor]) : super(executor ?? _open());

  /// In-memory constructor for tests (no `sqlite3_flutter_libs` / file I/O).
  AppDatabase.forTesting(super.executor);

  @override
  int get schemaVersion => 2;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) => m.createAll(),
        onUpgrade: (m, from, to) async {
          if (from < 2) {
            await m.createTable(starredContests);
            await m.createTable(platformRules);
            await m.createTable(scheduledReminders);
            await m.createTable(settings);
          }
        },
      );

  static QueryExecutor _open() =>
      driftDatabase(name: 'prognos_cache');

  Future<List<Contest>> allContests() => select(contests).get();

  // ─── Reminders: stars / rules / ledger ────────────────────────────────────

  Future<Set<String>> starredContestIds() async =>
      (await select(starredContests).get()).map((r) => r.contestId).toSet();

  Future<void> setStarred(String contestId, bool starred) async {
    if (starred) {
      await into(starredContests).insertOnConflictUpdate(
        StarredContestsCompanion.insert(contestId: contestId),
      );
    } else {
      await (delete(starredContests)
            ..where((t) => t.contestId.equals(contestId)))
          .go();
    }
  }

  Future<List<PlatformRule>> platformRulesList() =>
      select(platformRules).get();

  Future<Set<String>> enabledPlatforms() async =>
      (await (select(platformRules)..where((t) => t.enabled.equals(true))).get())
          .map((r) => r.platform)
          .toSet();

  Future<void> setPlatformRule(String platform, bool enabled) =>
      into(platformRules).insertOnConflictUpdate(
        PlatformRulesCompanion.insert(platform: platform, enabled: Value(enabled)),
      );

  Future<List<ScheduledReminder>> scheduledReminderList() =>
      (select(scheduledReminders)..orderBy([(t) => OrderingTerm(expression: t.fireAt)]))
          .get();

  Future<void> replaceScheduledReminders(List<ScheduledReminder> rows) async {
    await transaction(() async {
      await delete(scheduledReminders).go();
      await batch((b) => b.insertAll(scheduledReminders, rows));
    });
  }

  Future<String?> readSetting(String key) async {
    final row = await (select(settings)..where((t) => t.key.equals(key)))
        .getSingleOrNull();
    return row?.value;
  }

  Future<void> writeSetting(String key, String value) =>
      into(settings).insertOnConflictUpdate(
        SettingsCompanion.insert(key: key, value: value),
      );

  /// Wipe **user-scoped** local data on sign-out so a different account on the
  /// same device never sees the previous user's private analytics or reminders.
  /// The contests cache is left intact — it is public, non-personal data.
  Future<void> clearUserData() async {
    await transaction(() async {
      await delete(starredContests).go();
      await delete(platformRules).go();
      await delete(scheduledReminders).go();
      await (delete(settings)..where((t) => t.key.like('analytics.%'))).go();
      await (delete(settings)..where((t) => t.key.like('classrooms.%'))).go();
      await (delete(settings)
            ..where((t) => t.key.isIn(
                const ['reminder_lead_minutes', 'reminders_onboarded'])))
          .go();
    });
  }

  /// Replace the entire cached window with a fresh server result, atomically.
  /// The window returned by the backend is authoritative, so a full
  /// delete + reinsert keeps the cache identical to the last successful fetch
  /// (ended/removed contests fall out cleanly). Runs in one transaction, so a
  /// failure mid-write never leaves a partially-wiped cache.
  Future<void> replaceContests(List<Contest> rows) async {
    await transaction(() async {
      await delete(contests).go();
      await batch((b) => b.insertAll(contests, rows));
    });
  }
}
