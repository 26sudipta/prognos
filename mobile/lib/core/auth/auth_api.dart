import 'package:dio/dio.dart';

import 'app_user.dart';

/// Raw auth REST calls. Uses a plain [Dio] with the API base already configured.
/// The token endpoints are called with a *bare* Dio (no auth interceptor) to
/// avoid recursion during sign-in / refresh.
class AuthApi {
  AuthApi(this._dio);

  final Dio _dio;

  /// Exchange a Google ID token for a PROGNOS token pair.
  /// Returns `(accessToken, refreshToken)`.
  Future<(String, String)> googleMobile(String idToken) async {
    final res = await _dio.post(
      '/auth/google/mobile',
      data: {'id_token': idToken},
    );
    final d = res.data as Map<String, dynamic>;
    return (d['access_token'] as String, d['refresh_token'] as String);
  }

  /// Rotate the refresh token. Returns the new `(accessToken, refreshToken)`.
  /// The caller MUST persist the new refresh token (the old one is now revoked).
  Future<(String, String)> refreshMobile(String refreshToken) async {
    final res = await _dio.post(
      '/auth/refresh/mobile',
      data: {'refresh_token': refreshToken},
    );
    final d = res.data as Map<String, dynamic>;
    return (d['access_token'] as String, d['refresh_token'] as String);
  }

  /// Current user profile — also validates that an access token works.
  Future<AppUser> me(String accessToken) async {
    final res = await _dio.get(
      '/users/me',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
    return AppUser.fromJson(res.data as Map<String, dynamic>);
  }
}
