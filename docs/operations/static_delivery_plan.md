# GrassRoots Static Delivery and Release Plan

This plan covers the four production items:
1) where static files should live,
2) cache headers and versioning,
3) Django static config changes,
4) rollback-safe release flow.

## Recommended target architecture

## Primary recommendation (production)
- Django app serves dynamic requests only.
- Static assets are served from object storage + CDN.
- Media uploads are served from object storage (separate bucket/prefix from static).

## Practical topology
- Origin app: Django (Gunicorn/Uvicorn behind reverse proxy)
- Static origin: object storage bucket (e.g., S3/GCS)
- Static edge: CDN distribution in front of bucket
- Media origin: object storage bucket/prefix with controlled caching

## Why this is right for this repo
- Frontend artifacts are generated and change frequently.
- App includes large static/admin/dashboard surfaces.
- Offloading static reduces app server load and deploy risk.

## Cache and versioning policy

## Static assets (hashed)
- Use hashed filenames from Django static pipeline.
- Cache-Control: public, max-age=31536000, immutable
- CDN TTL: long (1 year) because filename hash changes on content change.

## HTML / dynamic responses
- Cache-Control: no-cache, no-store (or short max-age with revalidation policy)
- Do not apply immutable policy to HTML.

## Media uploads
- Cache-Control policy depends on object mutability:
  - immutable assets: long cache
  - user-replaceable assets: shorter cache, e.g. max-age=3600

## Versioning
- Use release tag + build timestamp in release metadata.
- Keep static manifests per release.
- Never overwrite hashed asset names; publish new assets each release.

## Django configuration changes (from current settings)

Current file: gr_project/settings.py
Current state includes:
- DEBUG=True
- CORS_ALLOW_ALL_ORIGINS=True
- STATIC_URL='static/'
- STATIC_ROOT=BASE_DIR/'staticfiles'

## Production changes required

## 1) Security/env controls
- Move sensitive values to environment variables.
- Set DEBUG from env and default to False in production.
- Restrict ALLOWED_HOSTS via env.
- Replace CORS_ALLOW_ALL_ORIGINS=True with explicit allowlist.

## 2) Static settings
- Set STATIC_URL to CDN URL in production, e.g. https://cdn.example.com/static/
- Keep STATIC_ROOT for collectstatic build output.
- Use Manifest storage for hashed filenames.

Suggested production settings snippet:

```python
import os

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]

STATIC_URL = os.getenv("DJANGO_STATIC_URL", "https://cdn.example.com/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}
```

If using cloud storage backend, replace staticfiles backend with the provider backend and keep manifest behavior via provider-compatible storage class.

## 3) Headers (proxy/CDN)
- Static responses: Cache-Control immutable policy.
- HTML/API responses: no-store/no-cache policy as required.
- Enable gzip/brotli for text assets.

## 4) Build/deploy static steps
- Build frontend artifacts.
- Run collectstatic in release pipeline.
- Upload/sync collected static to bucket prefix.
- Invalidate CDN only for non-hashed endpoints if needed.

## Rollback-safe release flow

## Pre-deploy
- Tag release commit.
- Build and publish static bundle for that tag.
- Record static manifest identifier.

## Deploy
1. Deploy app code.
2. Run migrations (only approved, with backup complete).
3. Switch traffic after health checks.

## Post-deploy verification
- Confirm homepage/admin/static assets all load via CDN.
- Confirm semantic dashboard routes render with no missing assets.
- Confirm no spike in 404 for static URLs.

## Rollback
1. Re-deploy previous app release tag.
2. Re-point to previous static manifest/bucket prefix.
3. Verify health checks and key flows.

Note: Rollback works best when each release has immutable static artifacts and explicit manifest mapping.

## Production TODOs (track to completion)
- [ ] Create production settings profile (or env-driven split) for gr_project.
- [ ] Add explicit allowed hosts and CORS allowlist env vars.
- [ ] Configure hashed static storage.
- [ ] Provision bucket + CDN and set DJANGO_STATIC_URL.
- [ ] Add release pipeline steps: build -> collectstatic -> upload -> verify.
- [ ] Add static 404 monitoring and dashboard.
- [ ] Test rollback using previous release + previous static manifest.
