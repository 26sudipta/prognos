import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Encrypted key-value store (Android Keystore / iOS Keychain) for the refresh
/// token and other secrets. Wired in M0; the auth flow (M1) reads/writes the
/// token pair through this.
class SecureStore {
  SecureStore(this._storage);

  final FlutterSecureStorage _storage;

  static const _kRefreshToken = 'refresh_token';

  Future<String?> readRefreshToken() => _storage.read(key: _kRefreshToken);

  Future<void> writeRefreshToken(String token) =>
      _storage.write(key: _kRefreshToken, value: token);

  Future<void> clear() => _storage.deleteAll();
}

final secureStoreProvider = Provider<SecureStore>((ref) {
  // flutter_secure_storage v10+ encrypts by default (Keystore/Keychain);
  // no per-platform options needed.
  return SecureStore(const FlutterSecureStorage());
});
