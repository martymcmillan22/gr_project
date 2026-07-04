class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'BTIF_API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );
}
