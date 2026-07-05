import 'dart:convert';

import '../db/app_database.dart';
import 'classroom_models.dart';
import 'classrooms_api.dart';

/// Cached-first classroom access. The classroom list and each leaderboard are
/// cached as JSON blobs in the drift `Settings` table (keys `classrooms.*`),
/// cleared on sign-out. Members/cohort/invites are fetched live (not cached).
class ClassroomsRepository {
  ClassroomsRepository(this.api, this._db);

  final ClassroomsApi api;
  final AppDatabase _db;

  static const _kList = 'classrooms.list';
  String _lbKey(String id) => 'classrooms.lb.$id';

  Future<List<Classroom>?> readCachedList() async {
    final raw = await _db.readSetting(_kList);
    if (raw == null) return null;
    return (jsonDecode(raw) as List<dynamic>)
        .map((e) => Classroom.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Classroom>> fetchList() async {
    final list = await api.list();
    await _db.writeSetting(_kList, jsonEncode([for (final c in list) c.toJson()]));
    return list;
  }

  Future<Leaderboard?> readCachedLeaderboard(String id) async {
    final raw = await _db.readSetting(_lbKey(id));
    if (raw == null) return null;
    return Leaderboard.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  Future<Leaderboard> fetchLeaderboard(String id) async {
    final lb = await api.leaderboard(id);
    await _db.writeSetting(_lbKey(id), jsonEncode(lb.toJson()));
    return lb;
  }
}
