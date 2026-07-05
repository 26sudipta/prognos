/// Authenticated user profile (from `GET /api/v1/users/me`).
class AppUser {
  const AppUser({
    required this.id,
    required this.email,
    required this.name,
    this.avatarUrl,
  });

  final String id;
  final String email;
  final String name;
  final String? avatarUrl;

  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
        id: json['id'] as String,
        email: json['email'] as String,
        name: (json['name'] as String?) ?? '',
        avatarUrl: json['avatar_url'] as String?,
      );

  /// Serialized for the offline profile cache (see [SecureStore.writeUser]).
  /// Uses the same keys as the API so [AppUser.fromJson] round-trips.
  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'name': name,
        'avatar_url': avatarUrl,
      };
}
