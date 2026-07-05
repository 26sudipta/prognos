import 'package:dio/dio.dart';

import '../auth/auth_api.dart';
import '../auth/token_store.dart';
import '../storage/secure_store.dart';

/// Injects the Bearer access token and transparently refreshes it once on a 401,
/// mirroring the web `_lib/api.ts`. Extends [QueuedInterceptor] so concurrent
/// requests during a refresh are serialized — only one refresh fires.
class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor(this._accessTokenStore, this._secureStore, this._refreshApi);

  final AccessTokenStore _accessTokenStore;
  final SecureStore _secureStore;
  final AuthApi _refreshApi;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = _accessTokenStore.token;
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final is401 = err.response?.statusCode == 401;
    final alreadyRetried = err.requestOptions.extra['__retried__'] == true;

    if (!is401 || alreadyRetried) {
      return handler.next(err);
    }

    final refresh = await _secureStore.readRefreshToken();
    if (refresh == null) {
      return handler.next(err);
    }

    try {
      final (access, newRefresh) = await _refreshApi.refreshMobile(refresh);
      // Rotation revokes the old token — persist the new one immediately.
      _accessTokenStore.token = access;
      await _secureStore.writeRefreshToken(newRefresh);

      final req = err.requestOptions;
      req.extra['__retried__'] = true;
      req.headers['Authorization'] = 'Bearer $access';
      final clone = await Dio().fetch<dynamic>(req);
      return handler.resolve(clone);
    } on DioException catch (e) {
      // Only a genuine auth rejection (the refresh token is dead) should end the
      // session. A network error during refresh is transient — keep the tokens
      // so a later attempt can recover, and just let this 401 surface.
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        _accessTokenStore.clear();
        await _secureStore.clear();
      }
      return handler.next(err);
    } catch (_) {
      return handler.next(err);
    }
  }
}
