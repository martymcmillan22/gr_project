# BTIF Deploy Checklist

## 1) Environment configuration
- Set `BTIF_SECRET_KEY` to a strong unique value.
- Set `BTIF_DEBUG=False` in production.
- Set `BTIF_ALLOWED_HOSTS` to real domains and hostnames.
- Set `BTIF_APP_VERSION` to your release version.

## 2) CORS restrictions
- Keep `BTIF_CORS_ALLOW_ALL_ORIGINS=False` in production.
- Set `BTIF_CORS_ALLOWED_ORIGINS` to known frontend origins only.
- Optionally set `BTIF_CORS_ALLOWED_ORIGIN_REGEXES` for controlled localhost or preview patterns.

## 3) API health verification
- Verify `GET /health/` returns:
  - `project: BTIF`
  - `status: ok`
  - expected `version`
- Verify `GET /api/subjects/` succeeds from allowed frontend origins.

## 4) Security and auth
- Verify token login and revoke endpoints function in target environment.
- Ensure admin access is restricted and protected.
- Use HTTPS in production and terminate TLS at your edge or load balancer.

## 5) Database and static assets
- Run migrations: `python manage.py migrate`
- Collect static files: `python manage.py collectstatic --noinput`

## 6) Smoke tests
- Register/login flow from Flutter frontend
- `/api/lattice-map/` returns data
- `/api/lattice-map/export/?export=csv` returns CSV
- Logout/revoke invalidates token
