# GrassRoots AWS Implementation Plan

This plan turns the AWS recommendation into actionable milestones.

## Chosen v1 path
- EC2 + Nginx + Gunicorn
- RDS PostgreSQL
- S3 + CloudFront for static
- Separate S3 bucket for media
- `gr_project.settings_production` for production-style settings

## Milestone 0: Decide and freeze the architecture
**Goal:** lock the first-release shape before provisioning.

### Tasks
- [ ] Confirm EC2 is the first compute choice.
- [ ] Confirm RDS PostgreSQL is the database.
- [ ] Confirm S3 + CloudFront is the static delivery model.
- [ ] Confirm media uses a separate S3 bucket.
- [ ] Confirm ECS/Fargate is deferred.

### Exit criteria
- One deployment path agreed.
- No unresolved architecture branches.

## Milestone 1: Prepare staging foundations
**Goal:** provision a safe staging mirror of production.

### Tasks
- [ ] Create staging VPC, subnet, and security groups.
- [ ] Create staging EC2 instance.
- [ ] Create staging RDS PostgreSQL instance.
- [ ] Create staging S3 static bucket.
- [ ] Create staging S3 media bucket.
- [ ] Create staging CloudFront distribution.
- [ ] Provision staging ACM certificate if needed.
- [ ] Set up IAM roles for staging app and CI/CD.

### Exit criteria
- Staging infrastructure exists and is reachable.
- Security groups are least-privilege.

## Milestone 2: Wire staging configuration
**Goal:** make the app run in staging with production-style settings.

### Tasks
- [ ] Set `DJANGO_SETTINGS_MODULE` for staging.
- [ ] Set `DJANGO_ALLOWED_HOSTS` for staging.
- [ ] Set `DJANGO_STATIC_URL` to CloudFront staging URL.
- [ ] Set `DJANGO_MEDIA_URL` to staging media URL.
- [ ] Store secrets in SSM Parameter Store or another secure source.
- [ ] Validate `gr_project.settings_production` or staging variant.

### Exit criteria
- App boots with staging settings.
- No hardcoded secrets required.

## Milestone 3: Static and media delivery
**Goal:** verify hashed static delivery and media separation.

### Tasks
- [ ] Build frontend assets.
- [ ] Run `collectstatic`.
- [ ] Upload static assets to staging S3.
- [ ] Verify CloudFront serves static assets.
- [ ] Confirm cache headers for hashed assets.
- [ ] Confirm media bucket is separate and accessible as intended.

### Exit criteria
- Static assets load from CloudFront.
- Media path is isolated from static.

## Milestone 4: Database safety and migrations
**Goal:** prove schema changes are safe in staging.

### Tasks
- [ ] Snapshot the staging database before migration testing.
- [ ] Run migrations in staging.
- [ ] Confirm schema changes do not break app startup.
- [ ] Verify fixture/seed loading if used.
- [ ] Document rollback procedure for migration failures.

### Exit criteria
- Migrations apply cleanly.
- Rollback approach is known and rehearsable.

## Milestone 5: App runtime and reverse proxy
**Goal:** run Django behind the actual serving stack.

### Tasks
- [ ] Start Gunicorn successfully.
- [ ] Configure Nginx to proxy to Gunicorn.
- [ ] Confirm HTTPS termination path.
- [ ] Confirm `/health/` endpoint works.
- [ ] Confirm admin loads with all static assets.

### Exit criteria
- App is serving real traffic paths in staging.
- No proxy/static regressions.

## Milestone 6: Feature smoke tests
**Goal:** validate the user-facing functionality that matters most.

### Tasks
- [ ] Story save works.
- [ ] STORY_INDEX auto-sync works.
- [ ] Semantic search returns expected results.
- [ ] Diff viewer renders correctly.
- [ ] Heatmap renders 4 timeline phases.
- [ ] Transitional Delta Strip renders correctly.
- [ ] Preset CRUD works.

### Exit criteria
- Core feature set passes smoke checks.
- No critical UX regressions.

## Milestone 7: Observability and rollback rehearsal
**Goal:** make sure failure can be seen and reversed.

### Tasks
- [ ] Enable CloudWatch logs.
- [ ] Configure alarms for app and RDS health.
- [ ] Confirm static 404 monitoring.
- [ ] Rehearse app rollback to previous version.
- [ ] Rehearse static rollback to previous release.
- [ ] Rehearse database snapshot restore plan.

### Exit criteria
- Rollback is tested, not theoretical.
- Alerts are available before production.

## Milestone 8: Production dry run
**Goal:** prove the release path without changing production yet.

### Tasks
- [ ] Run backend checks.
- [ ] Run frontend build.
- [ ] Run backend test suite.
- [ ] Run staging smoke tests again from clean state.
- [ ] Confirm production settings pass validation.
- [ ] Review the pre-production stability checklist.

### Exit criteria
- All gates are green.
- No unresolved blockers remain.

## Milestone 9: Production cutover readiness
**Goal:** move from staging validation to launch readiness.

### Tasks
- [ ] Confirm release branch is frozen.
- [ ] Confirm DB snapshot strategy is ready.
- [ ] Confirm static versioning and rollback are documented.
- [ ] Confirm approval/sign-off workflow.
- [ ] Only then schedule production launch.

### Exit criteria
- Launch can happen without improvisation.
- Rollback steps are already written.

## Recommended order of execution
1. Freeze architecture choice.
2. Provision staging infrastructure.
3. Wire config/secrets.
4. Validate static/media.
5. Validate migrations.
6. Run runtime and feature smoke tests.
7. Rehearse rollback.
8. Run a dry production gate.
9. Stop and fix anything that fails before production.

## Notes
- Keep `STATIC_URL` stable and use hashed filenames for cache safety.
- Prefer staging to mirror production topology as closely as budget allows.
- Do not move to production until the stability checklist is fully green.
