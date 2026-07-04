import 'package:flutter/material.dart';
import 'config/api_config.dart';
import 'models/auth_user.dart';
import 'services/btif_auth_service.dart';
import 'services/btif_browser_service.dart';
import 'services/session_storage_service.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BTIF Auth Preview',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const AppBootstrapPage(),
    );
  }
}

class AppBootstrapPage extends StatefulWidget {
  const AppBootstrapPage({super.key});

  @override
  State<AppBootstrapPage> createState() => _AppBootstrapPageState();
}

class _AppBootstrapPageState extends State<AppBootstrapPage> {
  final BtifAuthService _authService = BtifAuthService();
  final SessionStorageService _storage = SessionStorageService();

  Future<_BootResult> _bootstrap() async {
    final token = await _storage.readToken();
    if (token == null || token.isEmpty) {
      return const _BootResult.authRequired();
    }

    try {
      final user = await _authService.me(token);
      await _storage.saveSession(token: token, user: user);
      return _BootResult.authenticated(token: token, user: user);
    } catch (_) {
      await _storage.clearSession();
      return const _BootResult.authRequired();
    }
  }

  @override
  void dispose() {
    _authService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_BootResult>(
      future: _bootstrap(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final result = snapshot.data!;
        if (result.authenticated) {
          return SessionPage(token: result.token!, initialUser: result.user!);
        }
        return const AuthPage();
      },
    );
  }
}

class _BootResult {
  const _BootResult._({required this.authenticated, this.token, this.user});

  final bool authenticated;
  final String? token;
  final AuthUser? user;

  const _BootResult.authRequired() : this._(authenticated: false);

  const _BootResult.authenticated({
    required String token,
    required AuthUser user,
  }) : this._(authenticated: true, token: token, user: user);
}

class AuthPage extends StatefulWidget {
  const AuthPage({super.key});

  @override
  State<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends State<AuthPage> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailController = TextEditingController();
  final _service = BtifAuthService();
  final _storage = SessionStorageService();
  bool _loading = false;
  bool _rememberMe = true;
  String? _error;

  Future<void> _persistSession({
    required String token,
    required AuthUser user,
  }) async {
    if (_rememberMe) {
      await _storage.saveSession(token: token, user: user);
      return;
    }
    await _storage.clearSession();
  }

  Future<void> _login() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final token = await _service.login(
        username: _usernameController.text.trim(),
        password: _passwordController.text.trim(),
      );
      final user = await _service.me(token);
      await _persistSession(token: token, user: user);

      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => SessionPage(token: token, initialUser: user),
        ),
      );
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  Future<void> _register() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final session = await _service.register(
        username: _usernameController.text.trim(),
        password: _passwordController.text.trim(),
        email: _emailController.text.trim(),
      );
      await _persistSession(token: session.token, user: session.user);

      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) =>
              SessionPage(token: session.token, initialUser: session.user),
        ),
      );
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _emailController.dispose();
    _service.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('BTIF Auth Preview')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _usernameController,
              decoration: const InputDecoration(labelText: 'Username'),
              enabled: !_loading,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: 'Email (for register)',
              ),
              enabled: !_loading,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(labelText: 'Password'),
              obscureText: true,
              enabled: !_loading,
            ),
            const SizedBox(height: 24),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Remember me on this device'),
              value: _rememberMe,
              onChanged: _loading
                  ? null
                  : (value) {
                      setState(() {
                        _rememberMe = value ?? true;
                      });
                    },
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _loading ? null : _login,
                    child: _loading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              color: Colors.white,
                              strokeWidth: 2,
                            ),
                          )
                        : const Text('Login'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    onPressed: _loading ? null : _register,
                    child: const Text('Register'),
                  ),
                ),
              ],
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],
            const SizedBox(height: 16),
            const Text(
              'This screen uses /api/auth/register/ and /api/auth/token/.\n'
              'On success it loads /api/auth/me/ and supports token revoke.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              'API Base URL: ${ApiConfig.baseUrl}',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class SessionPage extends StatefulWidget {
  const SessionPage({
    super.key,
    required this.token,
    required this.initialUser,
  });

  final String token;
  final AuthUser initialUser;

  @override
  State<SessionPage> createState() => _SessionPageState();
}

class _SessionPageState extends State<SessionPage> {
  final BtifAuthService _service = BtifAuthService();
  final SessionStorageService _storage = SessionStorageService();
  late AuthUser _user;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _user = widget.initialUser;
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }

  Future<void> _refreshUser() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final user = await _service.me(widget.token);
      setState(() {
        _user = user;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  Future<void> _logout() async {
    try {
      await _service.revoke(widget.token);
      await _storage.clearSession();
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => const AuthPage()),
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Could not revoke token: $e')));
    }
  }

  void _openBrowser() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => BtifBrowserPage(token: widget.token),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BTIF Session'),
        actions: [
          IconButton(
            onPressed: _logout,
            icon: const Icon(Icons.logout),
            tooltip: 'Revoke Token and Exit',
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Logged In User',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text('ID: ${_user.id}'),
            Text('Username: ${_user.username}'),
            Text('Email: ${_user.email.isEmpty ? '(none)' : _user.email}'),
            const SizedBox(height: 16),
            const Text(
              'Token',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            SelectableText(widget.token),
            const SizedBox(height: 20),
            Row(
              children: [
                ElevatedButton(
                  onPressed: _loading ? null : _refreshUser,
                  child: _loading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text('Refresh /auth/me'),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  onPressed: _openBrowser,
                  child: const Text('Open BTIF Browser'),
                ),
              ],
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],
            const Spacer(),
            Text(
              'API Base URL: ${ApiConfig.baseUrl}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class BtifBrowserPage extends StatefulWidget {
  const BtifBrowserPage({super.key, required this.token});

  final String token;

  @override
  State<BtifBrowserPage> createState() => _BtifBrowserPageState();
}

class _BtifBrowserPageState extends State<BtifBrowserPage> {
  static const Map<String, String> _resourceEndpoints = {
    'Subjects': 'subjects/',
    'Branches': 'branches/',
    'Industries': 'industries/',
    'Sub-Industries': 'sub-industries/',
    'Temporal Slots': 'temporal-slots/',
    'Lattice Map': 'lattice-map/',
  };

  final BtifBrowserService _browserService = BtifBrowserService();
  final _subjectController = TextEditingController();
  final _branchController = TextEditingController();
  final _industryController = TextEditingController();
  final _tenseController = TextEditingController();
  final _phaseController = TextEditingController();
  final _positionController = TextEditingController();

  String _selectedResource = 'Subjects';
  bool _loading = false;
  String? _error;
  int _count = 0;
  List<dynamic> _results = [];

  @override
  void initState() {
    super.initState();
    _loadResource();
  }

  @override
  void dispose() {
    _browserService.dispose();
    _subjectController.dispose();
    _branchController.dispose();
    _industryController.dispose();
    _tenseController.dispose();
    _phaseController.dispose();
    _positionController.dispose();
    super.dispose();
  }

  Map<String, String> _buildFilters() {
    return {
      'subject': _subjectController.text,
      'branch': _branchController.text,
      'industry': _industryController.text,
      'tense': _tenseController.text,
      'phase': _phaseController.text,
      'position': _positionController.text,
    };
  }

  Future<void> _loadResource() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final endpoint = _resourceEndpoints[_selectedResource]!;
      final data = await _browserService.fetchResource(
        endpoint: endpoint,
        token: widget.token,
        filters: _buildFilters(),
      );

      setState(() {
        _count = (data['count'] ?? 0) as int;
        _results = (data['results'] ?? <dynamic>[]) as List<dynamic>;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  Future<void> _exportCsv() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final csv = await _browserService.exportLatticeCsv(
        token: widget.token,
        filters: _buildFilters(),
      );

      if (!mounted) return;
      final previewLines = csv.split('\n').take(12).join('\n');
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Lattice CSV Preview (first lines)'),
          content: SingleChildScrollView(child: SelectableText(previewLines)),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  String _asText(
    Map<String, dynamic> row,
    String key, {
    String fallback = '-',
  }) {
    final value = row[key];
    if (value == null) {
      return fallback;
    }
    final text = value.toString();
    return text.isEmpty ? fallback : text;
  }

  Widget _metaLine(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(top: 4.0),
      child: Text('$label: $value'),
    );
  }

  Widget _resultCard({
    required String title,
    required List<Widget> details,
    List<Widget> tags = const [],
  }) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            if (tags.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(spacing: 8, runSpacing: 8, children: tags),
            ],
            const SizedBox(height: 8),
            ...details,
          ],
        ),
      ),
    );
  }

  Widget _buildResultItem(Map<String, dynamic> row) {
    switch (_selectedResource) {
      case 'Subjects':
        return _resultCard(
          title: _asText(row, 'name'),
          tags: [
            Chip(label: Text('Acronym ${_asText(row, 'acronym')}')),
            Chip(label: Text('Order ${_asText(row, 'order')}')),
          ],
          details: [
            _metaLine(
              'Description',
              _asText(row, 'description', fallback: '(none)'),
            ),
          ],
        );

      case 'Branches':
        return _resultCard(
          title: _asText(row, 'name'),
          tags: [
            Chip(label: Text('Subject ${_asText(row, 'subject_name')}')),
            Chip(label: Text('Acronym ${_asText(row, 'acronym')}')),
            Chip(label: Text('Order ${_asText(row, 'order')}')),
          ],
          details: [
            _metaLine('Branch ID', _asText(row, 'id')),
            _metaLine('Subject ID', _asText(row, 'subject')),
          ],
        );

      case 'Industries':
        return _resultCard(
          title: _asText(row, 'name'),
          tags: [
            Chip(label: Text('Subject ${_asText(row, 'subject_name')}')),
            Chip(label: Text('Branch ${_asText(row, 'branch_name')}')),
            Chip(label: Text('Order ${_asText(row, 'order')}')),
          ],
          details: [
            _metaLine('Industry ID', _asText(row, 'id')),
            _metaLine('Branch ID', _asText(row, 'branch')),
          ],
        );

      case 'Sub-Industries':
        return _resultCard(
          title: _asText(row, 'name'),
          tags: [
            Chip(label: Text('Subject ${_asText(row, 'subject_name')}')),
            Chip(label: Text('Branch ${_asText(row, 'branch_name')}')),
            Chip(label: Text('Industry ${_asText(row, 'industry_name')}')),
            Chip(label: Text('Order ${_asText(row, 'order')}')),
          ],
          details: [
            _metaLine('Sub-Industry ID', _asText(row, 'id')),
            _metaLine('Industry ID', _asText(row, 'industry')),
          ],
        );

      case 'Temporal Slots':
        return _resultCard(
          title: 'Position ${_asText(row, 'position')}',
          tags: [
            Chip(label: Text('Tense ${_asText(row, 'tense')}')),
            Chip(label: Text('Color ${_asText(row, 'color')}')),
            Chip(label: Text('Phase ${_asText(row, 'default_phase')}')),
          ],
          details: [_metaLine('Temporal Slot ID', _asText(row, 'id'))],
        );

      case 'Lattice Map':
        return _resultCard(
          title: _asText(row, 'sub_industry'),
          tags: [
            Chip(label: Text('Position ${_asText(row, 'position')}')),
            Chip(label: Text('Tense ${_asText(row, 'tense')}')),
            Chip(label: Text('Color ${_asText(row, 'color')}')),
            Chip(label: Text('Phase ${_asText(row, 'phase')}')),
          ],
          details: [
            _metaLine('Subject', _asText(row, 'subject')),
            _metaLine('Branch', _asText(row, 'branch')),
            _metaLine('Industry', _asText(row, 'industry')),
            _metaLine('Sub-Industry Order', _asText(row, 'sub_industry_order')),
          ],
        );

      default:
        return _resultCard(
          title: 'Result',
          details: [SelectableText(row.toString())],
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('BTIF Resource Browser')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DropdownButtonFormField<String>(
              initialValue: _selectedResource,
              decoration: const InputDecoration(labelText: 'Resource'),
              items: _resourceEndpoints.keys
                  .map(
                    (name) => DropdownMenuItem(value: name, child: Text(name)),
                  )
                  .toList(),
              onChanged: _loading
                  ? null
                  : (value) {
                      if (value == null) return;
                      setState(() {
                        _selectedResource = value;
                      });
                    },
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                _FilterField(controller: _subjectController, label: 'subject'),
                _FilterField(controller: _branchController, label: 'branch'),
                _FilterField(
                  controller: _industryController,
                  label: 'industry',
                ),
                _FilterField(controller: _tenseController, label: 'tense'),
                _FilterField(controller: _phaseController, label: 'phase'),
                _FilterField(
                  controller: _positionController,
                  label: 'position',
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                ElevatedButton(
                  onPressed: _loading ? null : _loadResource,
                  child: const Text('Load'),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  onPressed: _loading ? null : _exportCsv,
                  child: const Text('Export Lattice CSV Preview'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text('Count: $_count'),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],
            const SizedBox(height: 8),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _results.isEmpty
                  ? const Center(child: Text('No results.'))
                  : ListView.builder(
                      itemCount: _results.length,
                      itemBuilder: (context, index) {
                        final row = _results[index] as Map<String, dynamic>;
                        return _buildResultItem(row);
                      },
                    ),
            ),
            const SizedBox(height: 8),
            Text(
              'API Base URL: ${ApiConfig.baseUrl}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _FilterField extends StatelessWidget {
  const _FilterField({required this.controller, required this.label});

  final TextEditingController controller;
  final String label;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 170,
      child: TextField(
        controller: controller,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          isDense: true,
        ),
      ),
    );
  }
}
