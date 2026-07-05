# GrassRoots Production Readiness Checklist

Use this as the final gate before any production deployment.

## Release Metadata
- Release version/tag:
- Release owner:
- Deployment window (local + UTC):
- Change summary:
- Linked PRs/issues:

## 1) Scope and Change Control
- [ ] Branching/PR process followed per docs/operations/version_control_system.md.
- [ ] Scope is frozen for this release.
- [ ] All release commits are merged to the release branch.
- [ ] Release notes are prepared.
- [ ] Rollback trigger conditions are agreed.

## 2) Environment and Secrets
- [ ] Production environment variables are present and validated.
- [ ] DEBUG is disabled.
- [ ] ALLOWED_HOSTS is production-safe.
- [ ] CSRF trusted origins are correct.
- [ ] SECRET_KEY and sensitive tokens are sourced from secrets manager.
- [ ] No secrets are hardcoded in tracked files.

## 3) Database and Migrations
- [ ] Migration list reviewed for risk and duration.
- [ ] Pre-deploy database backup/snapshot completed.
- [ ] Migration rollback plan documented.
- [ ] Migration tested in staging with production-like data shape.
- [ ] Data-loss operations explicitly reviewed and approved.

## 4) Dependency and Build Health
- [ ] Python dependencies are pinned and install cleanly.
- [ ] Frontend dependencies install cleanly.
- [ ] Frontend production build succeeds.
- [ ] No unexpected new build warnings.
- [ ] Static assets pipeline is verified.

Suggested local checks:
- ./a_gr_venv/bin/python manage.py check
- ./a_gr_venv/bin/python manage.py test
- cd frontend_homepage && npm ci && npm run build

## 5) Application Quality Gates
- [ ] Critical backend tests pass.
- [ ] Critical frontend flows are smoke-tested.
- [ ] Story save and STORY_INDEX sync are verified.
- [ ] Semantic operations endpoints return expected results.
- [ ] Manual admin dashboard sanity check completed.

## 6) Security and Access
- [ ] Admin accounts and privileges reviewed.
- [ ] Session/cookie security settings verified for production.
- [ ] CORS policy reviewed for least privilege.
- [ ] Rate limiting / abuse controls reviewed.
- [ ] Audit logging and traceability are enabled.

## 7) Observability and Ops
- [ ] Error monitoring is enabled (and tested).
- [ ] Logs are centralized and searchable.
- [ ] Health checks are configured.
- [ ] Alerting thresholds are configured for key failures.
- [ ] On-call contact and escalation path confirmed.

## 8) Deployment Plan
- [ ] Deployment runbook is current.
- [ ] Exact deploy commands are validated.
- [ ] Maintenance/communication notice prepared (if needed).
- [ ] Rollback commands tested and ready.
- [ ] Post-deploy verification script/checklist prepared.

## 9) Post-Deploy Verification
- [ ] App responds on production URL.
- [ ] Authentication/login works.
- [ ] Story engine core actions succeed.
- [ ] Static files and media load correctly.
- [ ] Background jobs/schedulers are healthy.
- [ ] No critical errors in logs after deployment.

## 10) Sign-Off
- [ ] Engineering sign-off
- [ ] Product/Owner sign-off
- [ ] Operations sign-off

Sign-off notes:

