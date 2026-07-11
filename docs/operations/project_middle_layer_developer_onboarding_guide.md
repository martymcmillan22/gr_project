# Project Middle Layer Developer Onboarding Guide

Audience: New engineers implementing, extending, or operating Project Middle Layer.

## 1. What You Are Joining

Project Middle Layer is the semantic platform for deterministic project identity compilation, governance, and platform interoperability.

Key outcomes you should preserve:

- Deterministic semantic outputs.
- Auditability and permission safety.
- Cross-surface consistency (admin, API, CLI).
- Stable extension points (plugins, extensions, marketplace, external agents).

## 2. Local Setup

## Prerequisites

- Python virtual environment at a_gr_venv
- Django project rooted at repository root
- SQLite local db by default unless environment overrides

## Baseline Commands

```bash
./a_gr_venv/bin/python manage.py migrate
./a_gr_venv/bin/python manage.py check
./a_gr_venv/bin/python manage.py test project_middle_layer
```

## Optional Demo Seed

```bash
./a_gr_venv/bin/python manage.py project_middle_layer_seed_phase10
```

## 3. Environment and Permissions

Use .env.example and docs/operations/environment_profiles.md for profile baselines.

Critical flag:

- PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS

Guidance:

- local: false (developer convenience)
- staging/production: true

For Phase 10 role seeding and capability bundles:

- docs/operations/project_middle_layer_phase10_roles.md

## 4. Repository Landmarks

Core app:

- project_middle_layer/

Primary domains:

- models/: semantic entities and platform records
- api/: serializers, views, routes
- views.py + templates/admin/: operator surfaces
- management/commands/: CLI operations and deterministic seed tools
- tests.py: route, API, admin, and strict permission tests

Docs to read first:

- docs/architecture/project_middle_layer_semantic_architecture_overview.md
- docs/architecture/project_middle_layer_platform_release_notes_phase1_to_phase10.md

## 5. Daily Development Workflow

1. Pull latest branch and re-run tests.
2. Build changes in one surface first (usually service/model).
3. Wire API/admin/CLI parity where needed.
4. Add tests for behavior and permission gating.
5. Run focused tests, then full project_middle_layer suite.
6. Verify strict mode behavior for mutating actions.

## 6. Common Task Playbooks

## Add a New Semantic Operation

- Implement service-level function in project_middle_layer/.
- Add capability gate where mutation is possible.
- Expose via API serializer/view/route if externally needed.
- Expose via admin view/template if operator-facing.
- Add CLI action if automation is expected.
- Add tests for success + permission denied + error path.

## Add a New Platform Capability

- Define capability key and intended role mapping.
- Update role seed strategy and docs.
- Enforce in API/admin/CLI entry points.
- Add strict-permission tests.

## Add a New Platformization Entity

- Add model and migration.
- Add deterministic service layer.
- Add admin/API surfaces and tests.
- Add seed data if needed for operator preview.

## 7. Testing Strategy

Run sequence:

```bash
./a_gr_venv/bin/python manage.py test project_middle_layer.tests.ProjectMiddleLayerAdminTests --keepdb
./a_gr_venv/bin/python manage.py test project_middle_layer
```

Expectations:

- New admin controls should have admin-page tests.
- New API actions should have strict-mode allow/deny coverage.
- New CLI actions should validate payload and capability behavior.

## 8. Coding and Review Rules

- Preserve deterministic behavior and explicit schema handling.
- Avoid hidden side effects in views; keep business logic in service modules.
- Keep mutating actions auditable.
- Avoid broad refactors unrelated to the feature.
- Do not revert unrelated user changes in a dirty working tree.

## 9. Phase 10-Specific Operator/Developer Notes

Key operations to know:

- marketplace install
- plugin register/toggle
- extension apply/rollback
- gateway introspect/dispatch
- btif export/validate
- external agent register/run
- cross-platform sync run

All should remain capability-gated, auditable, and test-backed.

## 10. First Week Checklist

- Run local setup and full tests.
- Read architecture and release notes docs.
- Seed Phase 10 demo data.
- Walk through Project Middle Layer admin pages.
- Execute one API call and one CLI command per Phase 10 area.
- Submit one small change with tests and strict-mode validation.
