import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

class BtifBrowserService {
  BtifBrowserService({http.Client? client, String? baseUrl})
    : _client = client ?? http.Client(),
      _baseUrl = baseUrl ?? ApiConfig.baseUrl;

  final http.Client _client;
  final String _baseUrl;

  Future<Map<String, dynamic>> fetchResource({
    required String endpoint,
    required String token,
    Map<String, String> filters = const {},
  }) async {
    final uri = Uri.parse(
      '$_baseUrl/api/$endpoint',
    ).replace(queryParameters: _normalizedFilters(filters));

    final response = await _client.get(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    throw Exception('Fetch failed: ${response.statusCode} ${response.body}');
  }

  Future<String> exportLatticeCsv({
    required String token,
    Map<String, String> filters = const {},
  }) async {
    final query = {..._normalizedFilters(filters), 'export': 'csv'};
    final uri = Uri.parse(
      '$_baseUrl/api/lattice-map/export/',
    ).replace(queryParameters: query);

    final response = await _client.get(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token',
      },
    );

    if (response.statusCode == 200) {
      return response.body;
    }

    throw Exception(
      'CSV export failed: ${response.statusCode} ${response.body}',
    );
  }

  Map<String, String> _normalizedFilters(Map<String, String> filters) {
    final normalized = <String, String>{};
    for (final entry in filters.entries) {
      final value = entry.value.trim();
      if (value.isNotEmpty) {
        normalized[entry.key] = value;
      }
    }
    return normalized;
  }

  void dispose() {
    _client.close();
  }
}
