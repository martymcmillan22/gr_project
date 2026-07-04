import 'auth_user.dart';

class AuthSession {
  const AuthSession({required this.token, required this.user});

  final String token;
  final AuthUser user;

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    final userJson =
        (json['user'] ?? <String, dynamic>{}) as Map<String, dynamic>;
    return AuthSession(
      token: (json['token'] ?? '') as String,
      user: AuthUser.fromJson(userJson),
    );
  }
}
