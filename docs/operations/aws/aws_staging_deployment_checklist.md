# GrassRoots AWS Staging Deployment Checklist

Use this checklist to validate the first AWS release path before any production cutover.

## Recommended v1 stack
- EC2 + Nginx + Gunicorn
- RDS PostgreSQL
- S3 + CloudFront for static
- Separate S3 bucket for media
- `gr_project.settings_production` for production-style config

## 1) Foundation Setup
- [ ] Confirm EC2 as the first compute choice.
- [ ] Confirm RDS PostgreSQL as the database.
- [ ] Confirm S3 + CloudFront for static assets.
- [ ] Confirm separate S3 bucket for media.
- [ ] Confirm staging and production will use the same topology.
- [ ] Confirm least-privilege IAM roles exist for app and CI/CD.

## 2) Staging Environment Provisioning
- [ ] Create staging VPC/subnets/security groups.
- [ ] Create staging EC2 instance.
- [ ] Create staging RDS PostgreSQL instance.
- [ ] Create staging S3 static bucket.
- [ ] Create staging S3 media bucket.
- [ ] Create staging CloudFront distribution for static.
- [ ] Provision ACM certificate for staging domain if needed.

## 3) Application Configuration
- [ ] Use `gr_project.settings_production` or a staging variant derived from it.
- [ ] Set `DJANGO_SETTINGS_MODULE` in staging.
- [ ] Set `DJANGO_ALLOWED_HOSTS` for staging.
- [ ] Set `DJANGO_STATIC_URL` to the staging CloudFront URL.
- [ ] Set `DJANGO_MEDIA_URL` to the staging media URL.
- [ ] Store secrets in SSM Parameter Store or equivalent secure storage.

## 4) Static Delivery Setup
- [ ] Build frontend assets successfully.
- [ ] Run Django `collectstatic` with staging settings.
- [ ] Verify hashed static filenames are generated.
- [ ] Upload static assets to the staging S3 bucket.
- [ ] Confirm CloudFront serves static assets correctly.
- [ ] Confirm cache headers are correct for hashed assets.

## 5) Database Safety
- [ ] Create staging DB snapshot before first migration.
- [ ] Run migrations in staging.
- [ ] Verify rollback plan before applying any risky schema change.
- [ ] Confirm fixtures/seed data load successfully.

## 6) Runtime Validation
- [ ] Start Gunicorn successfully on staging EC2.
- [ ] Confirm Nginx proxies requests to the app.
- [ ] Confirm `/health/` or equivalent endpoint returns healthy.
- [ ] Confirm login/session flow works.
- [ ] Confirm admin loads without missing static assets.

## 7) Core Feature Smoke Tests
- [ ] Story save path works.
- [ ] STORY_INDEX auto-sync works.
- [ ] Semantic search returns results.
- [ ] Semantic diff renders correctly.
- [ ] Heatmap renders 4 phases correctly.
- [ ] Transitional Delta Strip renders correctly.
- [ ] Presets create/load/delete correctly.

## 8) Observability
- [ ] CloudWatch logging enabled.
- [ ] Error tracking enabled if configured.
- [ ] Health check alarm configured.
- [ ] Static 404 alarm or equivalent monitored.
- [ ] RDS CPU/connection alarms configured.

## 9) Rollback Rehearsal
- [ ] Previous app version available.
- [ ] Previous static release available.
- [ ] Database snapshot restore tested or at least rehearsal documented.
- [ ] Rollback steps documented and timed.

## 10) Exit Criteria for Staging
- [ ] No blocking defects remain.
- [ ] Backend checks pass.
- [ ] Frontend build passes.
- [ ] Backend tests pass.
- [ ] Staging smoke tests pass.
- [ ] Ready for a production dry run.

## Recommended execution order
1. Provision staging infrastructure.
2. Configure app settings and secrets.
3. Deploy code.
4. Run migrations.
5. Collect and upload static assets.
6. Smoke test application flows.
7. Rehearse rollback.
8. Only then prepare the production cutover plan.
