class AuthUser {
  const AuthUser({
    required this.id,
    required this.username,
    required this.email,
  });

  final int id;
  final String username;
  final String email;

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id'] as int,
      username: (json['username'] ?? '') as String,
      email: (json['email'] ?? '') as String,
    );
  }
}
