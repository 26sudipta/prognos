/// Compile-time configuration. Override per build with `--dart-define`, e.g.
/// `flutter run --dart-define=API_BASE_URL=https://prognos-api.onrender.com`.
///
/// Default targets the local backend as seen from an Android emulator
/// (`10.0.2.2` is the host loopback). Physical devices / iOS use the LAN IP or
/// the deployed URL via --dart-define.
abstract final class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const String apiPrefix = '/api/v1';

  /// The PROGNOS **web** OAuth client id. Native Google Sign-In requests the ID
  /// token with this as the `serverClientId`, so the token's audience matches
  /// what the backend verifies (`GOOGLE_CLIENT_ID`). Public value (not a secret);
  /// overridable with --dart-define=GOOGLE_SERVER_CLIENT_ID=...
  static const String googleServerClientId = String.fromEnvironment(
    'GOOGLE_SERVER_CLIENT_ID',
    defaultValue:
        '238081955675-mn2fhn9q9von6g102h1kfo056j4fpdlu.apps.googleusercontent.com',
  );

  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 15);
}
