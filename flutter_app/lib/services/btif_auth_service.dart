import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../models/auth_session.dart';
import '../models/auth_user.dart';

class BtifAuthService {
  BtifAuthService({http.Client? client, String? baseUrl})
    : _client = client ?? http.Client(),
      _baseUrl = baseUrl ?? ApiConfig.baseUrl;

  final http.Client _client;
  final String _baseUrl;

  Future<AuthSession> register({
    required String username,
    required String password,
    String email = '',
  }) async {
    final uri = Uri.parse('$_baseUrl/api/auth/register/');
    final response = await _client.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
        'email': email,
      }),
    );

    if (response.statusCode == 201) {
      return AuthSession.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
    }

    throw Exception('Register failed: ${response.statusCode} ${response.body}');
  }

  Future<String> login({
    required String username,
    required String password,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/auth/token/');
    final response = await _client.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );

    if (response.statusCode == 200) {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      return body['token'] as String;
    }

    throw Exception('Login failed: ${response.statusCode} ${response.body}');
  }

  Future<AuthUser> me(String token) async {
    final uri = Uri.parse('$_baseUrl/api/auth/me/');
    final response = await _client.get(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token',
      },
    );

    if (response.statusCode == 200) {
      return AuthUser.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
    }

    throw Exception(
      'Fetching current user failed: ${response.statusCode} ${response.body}',
    );
  }

  Future<void> revoke(String token) async {
    final uri = Uri.parse('$_baseUrl/api/auth/token/revoke/');
    final response = await _client.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token',
      },
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Token revoke failed: ${response.statusCode} ${response.body}',
      );
    }
  }

  void dispose() {
    _client.close();
  }
}
