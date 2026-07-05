import 'package:flutter_riverpod/flutter_riverpod.dart';

/// In-memory holder for the short-lived access token. Kept out of persistent
/// storage on purpose (only the long-lived refresh token is persisted, in the
/// OS keystore via [SecureStore]). Shared by the auth repository (writes) and
/// the Dio interceptor (reads).
class AccessTokenStore {
  String? token;

  void clear() => token = null;
}

final accessTokenStoreProvider = Provider<AccessTokenStore>((ref) => AccessTokenStore());
