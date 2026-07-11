# Environment Profiles

Recommended baseline values for common deployment profiles.

## Project Middle Layer and Core Django

| Variable | Local (dev) | Staging | Production |
|---|---|---|---|
| DJANGO_SETTINGS_MODULE | gr_project.settings | gr_project.settings_production | gr_project.settings_production |
| DEBUG | true (from gr_project.settings) | false | false |
| PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS | false | true | true |

## Security and Host Controls

| Variable | Local (dev) | Staging | Production |
|---|---|---|---|
| DJANGO_ALLOWED_HOSTS | localhost,127.0.0.1 | staging hostnames only | production hostnames only |
| DJANGO_CORS_ALLOWED_ORIGINS | local frontend origins | staging frontend origins | production frontend origins |
| DJANGO_CSRF_TRUSTED_ORIGINS | local app origins | staging app origins | production app origins |
| DJANGO_SECURE_SSL_REDIRECT | false | true | true |
| DJANGO_SESSION_COOKIE_SECURE | false | true | true |
| DJANGO_CSRF_COOKIE_SECURE | false | true | true |
| DJANGO_SECURE_HSTS_SECONDS | 0 | 300 | 31536000 |

## Notes

- Use local-only values for development convenience and faster iteration.
- Keep staging behavior close to production for permission and security checks.
- In production, keep strict permissions enabled and HTTPS/security flags enforced.
- Copy-paste ready profile blocks are also available in `.env.example`.
