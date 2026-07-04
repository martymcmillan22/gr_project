import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models/creative_idea.dart';

class ApiService {
  static const _baseUrl = 'http://127.0.0.1:8000';

  Future<String> login(String username, String password) async {
    final uri = Uri.parse('$_baseUrl/api/login/');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );

    if (response.statusCode == 200) {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      return body['token'] as String;
    }

    throw Exception('Login failed: ${response.statusCode} ${response.reasonPhrase}');
  }

  Future<List<CreativeIdea>> fetchIdeas(String token) async {
    final uri = Uri.parse('$_baseUrl/api/ideas/');
    final response = await http.get(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token',
      },
    );

    if (response.statusCode == 200) {
      final body = jsonDecode(response.body) as List<dynamic>;
      return body.map((item) => CreativeIdea.fromJson(item as Map<String, dynamic>)).toList();
    }

    throw Exception('Failed to load ideas: ${response.statusCode} ${response.reasonPhrase}');
  }

  Future<CreativeIdea> createIdea(String token, String content) async {
    final uri = Uri.parse('$_baseUrl/api/ideas/');
    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token',
      },
      body: jsonEncode({'content': content}),
    );

    if (response.statusCode == 201) {
      return CreativeIdea.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }

    throw Exception('Failed to create idea: ${response.statusCode} ${response.reasonPhrase}');
  }
}
