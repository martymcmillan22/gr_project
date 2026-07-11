# Project Middle Layer Phase 10 Role and Seeding Guide

This document defines strict-permission capability bundles for the Phase 10 platformization layer and the recommended deterministic seed workflow.

## Capability Bundle

Use these capabilities for Phase 10 features:

- `manage.marketplace`
- `manage.plugins`
- `manage.extensions`
- `gateway.inspect`
- `gateway.dispatch`
- `btif.interop`
- `manage.external_agents`
- `sync.cross_platform`

## Recommended Roles

- `phase10-platform-operator`
: Full Phase 10 capability bundle.
- `phase10-platform-reviewer`
: Read/interoperability subset (`gateway.inspect`, `btif.interop`, `sync.cross_platform`).

## Seed Command

Seed roles and demo records with the management command:

```bash
./a_gr_venv/bin/python manage.py project_middle_layer_seed_phase10
```

Assign the operator role to a specific user profile while seeding:

```bash
./a_gr_venv/bin/python manage.py project_middle_layer_seed_phase10 --username <username>
```

Optional flags:

- `--skip-roles`
- `--skip-demo-data`

## Fixture Option

A static fixture is also provided:

- `fixtures/project_middle_layer_phase10_demo.json`

Load it with:

```bash
./a_gr_venv/bin/python manage.py loaddata fixtures/project_middle_layer_phase10_demo.json
```

## Notes

- Keep `PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=true` in staging and production.
- Roles are seeded with `update_or_create` for idempotency.
- Demo records are deterministic and safe to re-run.
