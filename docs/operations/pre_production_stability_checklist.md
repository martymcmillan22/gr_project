# GrassRoots Pre-Production Stability Checklist

Use this checklist before any production deployment. This is a stabilization gate, not a deploy runbook.

## Exit Criteria
- No critical defects open.
- No data-loss risk in planned migrations.
- All critical workflows pass smoke and regression checks.
- Build/check pipelines are green for backend and frontend.

## 1) Baseline Health
- [ ] Django system check passes.
- [ ] Frontend production build passes.
- [ ] No unexpected new warnings introduced by recent changes.

Suggested commands:
- `./a_gr_venv/bin/python manage.py check`
- `cd frontend_homepage && npm run build`

## 2) Database and Migration Safety
- [ ] New migrations apply cleanly in staging.
- [ ] Migration rollback approach is documented.
- [ ] Seed/fixture compatibility confirmed.
- [ ] Destructive operations reviewed and explicitly approved.

Suggested commands:
- `./a_gr_venv/bin/python manage.py showmigrations`
- `./a_gr_venv/bin/python manage.py migrate --plan`

## 3) Story Engine Regression Coverage
- [ ] Story save path writes expected content to MASTER_DOCUMENT.
- [ ] STORY_INDEX auto-sync still updates completed/placeholder rows correctly.
- [ ] Semantic metadata and version metadata persist correctly.

## 4) Semantic Ops Feature Validation
- [ ] Semantic search filters return expected results.
- [ ] Cluster modes (`mlas`, `timeline_phase`, `semantic_path`, `scaffold_version`, `dchd_cluster`) behave correctly.
- [ ] Diff viewer shows metadata/chapter/DCHD shifts correctly for selected entries.
- [ ] Preset create/load/delete works and persists.

## 5) Heatmap and Transitional Logic Validation
- [ ] Heatmap uses 4 phases only: `past`, `present-past`, `present-future`, `future`.
- [ ] Clicking a heatmap cell applies focused filters and refreshes context.
- [ ] Transitional Delta Strip values are directionally correct (present-past -> present-future).
- [ ] DCHD and version spread deltas render without errors.

## 6) Frontend and CSS Compatibility
- [ ] No new JSX parse warnings.
- [ ] CSS compatibility errors are resolved in platform dashboard styles.
- [ ] Responsive behavior checked on desktop and mobile widths.

## 7) Security/Configuration Readiness (Staging)
- [ ] `gr_project.settings_production` validates with staging-safe values.
- [ ] Host/CORS/CSRF env values are explicit and correct for staging.
- [ ] No secrets committed in git history/diff.

Suggested command:
- `./a_gr_venv/bin/python manage.py check --settings=gr_project.settings_production`

## 8) Release Dry Run
- [ ] Candidate release branch created.
- [ ] Full test/build/check run completed from clean working tree.
- [ ] Rollback rehearsal completed in staging.
- [ ] Known risks and mitigations documented.

## Sign-off
- Engineering:
- Product:
- Ops:
- Date:
