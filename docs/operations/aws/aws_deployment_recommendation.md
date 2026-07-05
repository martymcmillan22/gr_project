# GrassRoots AWS Deployment Recommendation

This document turns the AWS plan into a simpler first-release path.

## Recommendation

Use **EC2 + Nginx + Gunicorn** for the first production launch.

Why this path first:
- Lowest operational complexity.
- Easier to debug than container orchestration.
- Fits the current repo without forcing a container rewrite.
- Keeps deployment and rollback straightforward while the app is still stabilizing.

## What to defer until later
- ECS Fargate
- EKS
- Multi-region architecture
- Advanced autoscaling
- Complex container registry workflows

## Target v1 Architecture

### App layer
- EC2 instance running:
  - Nginx
  - Gunicorn
  - Django app
- Use `gr_project.settings_production` for production config.
- Use environment variables from SSM Parameter Store or a secured env file on the instance.

### Database
- RDS PostgreSQL, single-AZ to start.
- Prefer `db.t4g.small` for real production if budget allows.
- Use `db.t4g.micro` only for staging or very low traffic.
- Automated backups enabled.

### Static files
- S3 bucket for static assets.
- CloudFront in front of static bucket.
- Hashed static filenames via manifest storage.
- Fixed `DJANGO_STATIC_URL` pointing to CloudFront.

### Media files
- Separate S3 bucket for media uploads.
- Use private access or signed delivery if user-uploaded content is not public.
- Do not mix media with static.

### Networking and TLS
- One VPC.
- Public subnet for EC2.
- Security groups:
  - SSH locked down to admin IPs only (or SSM preferred).
  - Web traffic to Nginx on 80/443.
  - RDS accessible only from app security group.
- ACM certificate for HTTPS.
- Force HTTPS at the edge.

## Exact AWS Resource Set

### Required for launch
- EC2 instance
- EBS volume
- RDS PostgreSQL database
- S3 bucket for static
- S3 bucket for media
- CloudFront distribution for static
- IAM roles/policies for instance access
- SSM Parameter Store values or equivalent secret storage
- ACM certificate
- CloudWatch logs/alarms

### Nice to have later
- Elastic IP or load balancer
- Additional EC2 instance for failover
- RDS Multi-AZ
- CDN invalidation automation for non-hashed assets
- Sentry or other error tracking

## Production Settings Expectations

Use:
- `gr_project.settings_production`

Keep these values environment-driven:
- `DJANGO_SETTINGS_MODULE`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_STATIC_URL`
- `DJANGO_MEDIA_URL`
- `DATABASE_URL` or DB host/user/password settings

## Static Delivery Rules

- `STATIC_URL` should be stable and not change per release.
- Use hashed filenames so file content changes create new asset names.
- Use long-lived cache headers for hashed static assets.
- Media should use a separate cache policy.

## Release Flow for v1

1. Merge to release branch.
2. Run tests and build checks locally and in CI.
3. Create a DB snapshot.
4. Deploy app code to EC2.
5. Run migrations.
6. Run `collectstatic`.
7. Sync static assets to S3.
8. Update/restart Gunicorn and Nginx as needed.
9. Verify homepage, admin, story engine, and semantic ops.

## Rollback Flow

If the release fails:
1. Restore previous app code.
2. Revert to previous static build if needed.
3. Restore database snapshot only if a migration caused data loss or corruption.

## CI/CD for v1

Recommended GitHub Actions jobs:
- Backend check
- Backend tests
- Frontend build
- Deploy job (manual approval or tagged release)

Recommended deployment sequence:
- Build and test on PR.
- On tagged release, deploy to staging first.
- Promote to production only after smoke checks pass.

## Stability Gate Before Production

Do not launch until these pass:
- Django checks
- Production settings check
- Frontend build
- Django test suite
- Staging smoke tests
- Static/media verification
- Rollback rehearsal

## Why this works best for GrassRoots right now
- The app already has multiple Django apps and a frontend build.
- The team needs stability before complexity.
- EC2 keeps the first production launch understandable and debuggable.
- ECS can be a later optimization once release cadence and reliability are proven.

## Later migration path to ECS
- Containerize the app.
- Move runtime to ECS Fargate.
- Keep the same S3/CloudFront/RDS model.
- Reuse the same production settings and release gates.

## Immediate next steps
- [ ] Confirm EC2 as the v1 compute choice.
- [ ] Create staging AWS resources.
- [ ] Wire production secrets into SSM.
- [ ] Update deployment docs with exact commands.
- [ ] Build staging deployment and smoke test.
- [ ] Keep production blocked until stabilization gates pass.
