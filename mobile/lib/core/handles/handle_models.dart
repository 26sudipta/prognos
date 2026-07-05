/// The user's Codeforces handle link + verification status (`GET /handles`).
class Handle {
  const Handle({
    required this.id,
    required this.handle,
    required this.isVerified,
    required this.isLocked,
    this.lockoutExpiresAt,
    this.verificationToken,
    this.verificationTokenExpiresAt,
  });

  final String id;
  final String handle;
  final bool isVerified;
  final bool isLocked;
  final DateTime? lockoutExpiresAt;
  final String? verificationToken;
  final DateTime? verificationTokenExpiresAt;

  static DateTime? _dt(dynamic v) =>
      v == null ? null : DateTime.parse(v as String).toUtc();

  factory Handle.fromJson(Map<String, dynamic> j) => Handle(
        id: j['id'] as String,
        handle: j['handle'] as String,
        isVerified: j['is_verified'] == true,
        isLocked: j['is_locked'] == true,
        lockoutExpiresAt: _dt(j['lockout_expires_at']),
        verificationToken: j['verification_token'] as String?,
        verificationTokenExpiresAt: _dt(j['verification_token_expires_at']),
      );
}

/// Response of `POST /handles/verify/initiate`.
class HandleInitiation {
  const HandleInitiation({
    required this.handleId,
    required this.handle,
    required this.token,
    required this.expiresAt,
  });

  final String handleId;
  final String handle;
  final String token; // PGS-XXXXXX
  final DateTime expiresAt;

  factory HandleInitiation.fromJson(Map<String, dynamic> j) => HandleInitiation(
        handleId: j['handle_id'] as String,
        handle: j['handle'] as String,
        token: j['token'] as String,
        expiresAt: DateTime.parse(j['expires_at'] as String).toUtc(),
      );
}

/// Typed outcome of a failed confirm, so the controller can move to the right
/// state without leaking Dio into the UI.
enum ConfirmFailure { mismatch, locked, expired, notFound, unknown }

class ConfirmException implements Exception {
  const ConfirmException(this.kind, {this.attemptsRemaining});
  final ConfirmFailure kind;
  final int? attemptsRemaining;
}
