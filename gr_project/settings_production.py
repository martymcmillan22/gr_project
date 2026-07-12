"""Production settings overrides for GrassRoots.

Usage:
  DJANGO_SETTINGS_MODULE=gr_project.settings_production
"""

import os

from .settings import *  # noqa: F403,F401


def _csv_env(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# Core runtime security
DEBUG = False

# Prefer explicit production host config; fall back to existing base value if not provided.
ALLOWED_HOSTS = _csv_env("DJANGO_ALLOWED_HOSTS") or _csv_env("BTIF_ALLOWED_HOSTS") or ALLOWED_HOSTS  # noqa: F405

# CORS/CSRF hardening for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = _csv_env("DJANGO_CORS_ALLOWED_ORIGINS") or _csv_env("BTIF_CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _csv_env("DJANGO_CSRF_TRUSTED_ORIGINS")

# HTTPS and secure cookie policy
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true"
SESSION_COOKIE_SECURE = os.getenv("DJANGO_SESSION_COOKIE_SECURE", "True").lower() == "true"
CSRF_COOKIE_SECURE = os.getenv("DJANGO_CSRF_COOKIE_SECURE", "True").lower() == "true"
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", "True").lower() == "true"
SECURE_HSTS_PRELOAD = os.getenv("DJANGO_SECURE_HSTS_PRELOAD", "True").lower() == "true"
SECURE_REFERRER_POLICY = os.getenv("DJANGO_SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Static/media delivery
STATIC_URL = os.getenv("DJANGO_STATIC_URL", STATIC_URL)  # noqa: F405
MEDIA_URL = os.getenv("DJANGO_MEDIA_URL", MEDIA_URL)  # noqa: F405

# Use manifest hashing so static assets are cache-safe in CDN/object storage setups.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# Enforce strict semantic ACL behavior in production by default.
PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS = os.getenv("PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS", "true").lower() == "true"
