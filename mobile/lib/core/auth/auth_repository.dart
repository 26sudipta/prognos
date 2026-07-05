import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../config/app_config.dart';
import '../network/dio_client.dart';
import '../storage/secure_store.dart';
import 'app_user.dart';
import 'auth_api.dart';
import 'token_store.dart';

/// Orchestrates authentication: native Google Sign-In → backend token exchange →
/// token storage (access in memory, refresh in the OS keystore) → profile fetch.
class AuthRepository {
  AuthRepository(this._api, this._secureStore, this._accessTokenStore);

  final AuthApi _api;
  final SecureStore _secureStore;
  final AccessTokenStore _accessTokenStore;

  final GoogleSignIn _google = GoogleSignIn.instance;
  bool _googleInitialized = false;

  Future<void> _ensureGoogleInitialized() async {
    if (_googleInitialized) return;
    // serverClientId makes the ID token's audience the web client id, which is
    // what the backend verifies. Required on both Android and iOS.
    await _google.initialize(serverClientId: AppConfig.googleServerClientId);
    _googleInitialized = true;
  }

  /// Interactive sign-in. Returns the user, or `null` if the user canceled.
  Future<AppUser?> signInWithGoogle() async {
    await _ensureGoogleInitialized();

    final GoogleSignInAccount account;
    try {
      account = await _google.authenticate();
    } on GoogleSignInException catch (e) {
      if (e.code == GoogleSignInExceptionCode.canceled) return null;
      rethrow;
    }

    final idToken = account.authentication.idToken;
    if (idToken == null) {
      throw StateError('Google Sign-In returned no ID token');
    }

    final (access, refresh) = await _api.googleMobile(idToken);
    _accessTokenStore.token = access;
    await _secureStore.writeRefreshToken(refresh);
    final user = await _api.me(access);
    await _secureStore.writeUser(user); // cache for offline restore
    return user;
  }

  /// Silent session restore on launch.
  ///
  /// Distinguishes two failure modes, because conflating them wipes valid
  /// sessions offline:
  ///  • **Auth rejection** (401/403) → the refresh token is dead → clear and
  ///    route to login.
  ///  • **Network error** (offline / server down) → the session is fine → keep
  ///    the tokens and fall back to the cached profile so the app opens
  ///    offline. The [AuthInterceptor] silently re-auths on the first 401 once
  ///    connectivity returns.
  Future<AppUser?> restoreSession() async {
    final refresh = await _secureStore.readRefreshToken();
    if (refresh == null) return null;
    try {
      final (access, newRefresh) = await _api.refreshMobile(refresh);
      _accessTokenStore.token = access;
      await _secureStore.writeRefreshToken(newRefresh);
      final user = await _api.me(access);
      await _secureStore.writeUser(user);
      return user;
    } on DioException catch (e) {
      if (_isAuthRejection(e)) {
        await _secureStore.clear();
        _accessTokenStore.clear();
        return null;
      }
      // Offline: keep the session, open with the last-known profile (may be
      // null if we never cached one → login).
      return _secureStore.readUser();
    } catch (_) {
      await _secureStore.clear();
      _accessTokenStore.clear();
      return null;
    }
  }

  /// A response the server actually rejected on auth grounds — as opposed to a
  /// connection/timeout error, which carries no response.
  static bool _isAuthRejection(DioException e) {
    final code = e.response?.statusCode;
    return code == 401 || code == 403;
  }

  Future<void> signOut() async {
    try {
      await _ensureGoogleInitialized();
      await _google.signOut();
    } catch (_) {
      // Best-effort: local sign-out below is what actually matters.
    }
    _accessTokenStore.clear();
    await _secureStore.clear();
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    AuthApi(ref.watch(authDioProvider)),
    ref.watch(secureStoreProvider),
    ref.watch(accessTokenStoreProvider),
  );
});
