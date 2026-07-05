import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/auth/app_user.dart';
import 'package:prognos/core/auth/auth_api.dart';
import 'package:prognos/core/auth/auth_repository.dart';
import 'package:prognos/core/auth/token_store.dart';
import 'package:prognos/core/storage/secure_store.dart';

/// In-memory secure store (no platform keystore).
class _MemStore extends SecureStore {
  _MemStore() : super(const FlutterSecureStorage());
  final _m = <String, String>{};

  @override
  Future<String?> readRefreshToken() async => _m['refresh_token'];
  @override
  Future<void> writeRefreshToken(String token) async =>
      _m['refresh_token'] = token;
  @override
  Future<void> writeUser(AppUser user) async =>
      _m['user'] = jsonEncode(user.toJson());
  @override
  Future<AppUser?> readUser() async {
    final r = _m['user'];
    return r == null
        ? null
        : AppUser.fromJson(jsonDecode(r) as Map<String, dynamic>);
  }

  @override
  Future<void> clear() async => _m.clear();
}

/// AuthApi whose refresh always throws the given error.
class _ThrowingApi extends AuthApi {
  _ThrowingApi(this.error) : super(Dio());
  final DioException error;
  @override
  Future<(String, String)> refreshMobile(String refreshToken) async =>
      throw error;
}

DioException _connectionError() => DioException(
      requestOptions: RequestOptions(path: '/auth/refresh/mobile'),
      type: DioExceptionType.connectionError,
    );

DioException _unauthorized() {
  final opts = RequestOptions(path: '/auth/refresh/mobile');
  return DioException(
    requestOptions: opts,
    response: Response(requestOptions: opts, statusCode: 401),
    type: DioExceptionType.badResponse,
  );
}

void main() {
  const cachedUser = AppUser(id: 'u1', email: 'ada@x.io', name: 'Ada');

  test('offline restore keeps the session and returns the cached profile',
      () async {
    final store = _MemStore();
    await store.writeRefreshToken('rt');
    await store.writeUser(cachedUser);

    final repo =
        AuthRepository(_ThrowingApi(_connectionError()), store, AccessTokenStore());
    final user = await repo.restoreSession();

    // Gate gets a user → lands on the shell, not login.
    expect(user?.id, 'u1');
    // Credentials preserved for when connectivity returns.
    expect(await store.readRefreshToken(), 'rt');
  });

  test('a genuine auth rejection (401) clears the session', () async {
    final store = _MemStore();
    await store.writeRefreshToken('rt');
    await store.writeUser(cachedUser);

    final repo =
        AuthRepository(_ThrowingApi(_unauthorized()), store, AccessTokenStore());
    final user = await repo.restoreSession();

    expect(user, isNull);
    expect(await store.readRefreshToken(), isNull);
  });

  test('offline with no cached profile falls through to login', () async {
    final store = _MemStore();
    await store.writeRefreshToken('rt'); // token but never cached a user

    final repo =
        AuthRepository(_ThrowingApi(_connectionError()), store, AccessTokenStore());
    final user = await repo.restoreSession();

    expect(user, isNull);
    // Token still kept — a later online launch can restore.
    expect(await store.readRefreshToken(), 'rt');
  });
}
