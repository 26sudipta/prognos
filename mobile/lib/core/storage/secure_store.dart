import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../auth/app_user.dart';

/// Encrypted key-value store (Android Keystore / iOS Keychain) for the refresh
/// token and other secrets. Wired in M0; the auth flow (M1) reads/writes the
/// token pair through this.
class SecureStore {
  SecureStore(this._storage);

  final FlutterSecureStorage _storage;

  static const _kRefreshToken = 'refresh_token';
  static const _kUserProfile = 'user_profile';

  Future<String?> readRefreshToken() => _storage.read(key: _kRefreshToken);

  Future<void> writeRefreshToken(String token) =>
      _storage.write(key: _kRefreshToken, value: token);

  /// Cache the last-known profile so a **cold offline launch** can pass the auth
  /// gate without a network round-trip (M2). Cleared with the session on logout
  /// or a genuine auth rejection.
  Future<void> writeUser(AppUser user) =>
      _storage.write(key: _kUserProfile, value: jsonEncode(user.toJson()));

  Future<AppUser?> readUser() async {
    final raw = await _storage.read(key: _kUserProfile);
    if (raw == null) return null;
    try {
      return AppUser.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null; // corrupt cache → treat as absent
    }
  }

  Future<void> clear() => _storage.deleteAll();
}

final secureStoreProvider = Provider<SecureStore>((ref) {
  // flutter_secure_storage v10+ encrypts by default (Keystore/Keychain);
  // no per-platform options needed.
  return SecureStore(const FlutterSecureStorage());
});
