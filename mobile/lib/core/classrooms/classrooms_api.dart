import 'package:dio/dio.dart';

import 'classroom_models.dart';

/// Wrapper over `/classrooms/*` on the authed Dio.
class ClassroomsApi {
  ClassroomsApi(this._dio);
  final Dio _dio;

  Future<List<Classroom>> list() async {
    final res = await _dio.get<Map<String, dynamic>>('/classrooms');
    return ((res.data?['classrooms'] as List<dynamic>?) ?? const [])
        .map((e) => Classroom.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Classroom> create(String name) async {
    final res = await _dio.post<Map<String, dynamic>>('/classrooms',
        data: {'name': name});
    return Classroom.fromJson(res.data ?? const {});
  }

  Future<Classroom> get(String id) async {
    final res = await _dio.get<Map<String, dynamic>>('/classrooms/$id');
    return Classroom.fromJson(res.data ?? const {});
  }

  Future<void> delete(String id) => _dio.delete('/classrooms/$id');

  Future<Leaderboard> leaderboard(String id) async {
    final res =
        await _dio.get<Map<String, dynamic>>('/classrooms/$id/leaderboard');
    return Leaderboard.fromJson(res.data ?? const {});
  }

  Future<List<Member>> members(String id) async {
    final res = await _dio.get<Map<String, dynamic>>('/classrooms/$id/members');
    return ((res.data?['members'] as List<dynamic>?) ?? const [])
        .map((e) => Member.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CohortAnalytics> cohort(String id) async {
    final res = await _dio.get<Map<String, dynamic>>('/classrooms/$id/cohort');
    return CohortAnalytics.fromJson(res.data ?? const {});
  }

  Future<List<Invite>> invites(String id) async {
    final res = await _dio.get<Map<String, dynamic>>('/classrooms/$id/invites');
    return ((res.data?['invites'] as List<dynamic>?) ?? const [])
        .map((e) => Invite.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Invite> createInvite(String id) async {
    final res =
        await _dio.post<Map<String, dynamic>>('/classrooms/$id/invites');
    return Invite.fromJson(res.data ?? const {});
  }

  Future<void> revokeInvite(String id, String inviteId) =>
      _dio.delete('/classrooms/$id/invites/$inviteId');

  Future<void> removeMember(String id, String userId) =>
      _dio.delete('/classrooms/$id/members/$userId');

  Future<void> leave(String id) => _dio.delete('/classrooms/$id/members/me');

  Future<void> sync(String id) => _dio.post('/classrooms/$id/sync');

  Future<JoinPreview> joinPreview(String token) async {
    final res =
        await _dio.get<Map<String, dynamic>>('/classrooms/join-preview/$token');
    return JoinPreview.fromJson(res.data ?? const {});
  }

  Future<Classroom> join(String token) async {
    final res = await _dio.post<Map<String, dynamic>>('/classrooms/join',
        data: {'token': token});
    return Classroom.fromJson(res.data ?? const {});
  }
}
