# Project Middle Layer Operator Quickstart

## Goal

Get a semantic operator to first-value safely in one page: sign in, verify access, seed baseline data, run core actions, and confirm platform health.

## Prerequisites

- Local environment configured and app running
- Admin-capable account or a role with equivalent semantic capabilities
- Project Middle Layer migrations and phase data available

## 1. Verify Access and Roles

Confirm that your account has either:

- Superuser/staff privileges, or
- Semantic capabilities required for operator actions (for example: manage.marketplace, sync.cross_platform)

Reference: [Project Middle Layer Phase 10 Roles and Capability Seeding](project_middle_layer_phase10_roles.md)

## 2. Open the Operator Surface

Navigate to the Project Middle Layer admin page and confirm these sections load:

- Semantic health cards and trends
- Quick actions
- Alerts and lineage summaries
- Project node table and operational links

## 3. Seed Deterministic Baseline Data

Run the seed command to provision Phase 10 roles and demo platform objects:

```bash
./a_gr_venv/bin/python manage.py project_middle_layer_seed_phase10
```

Or use the one-click admin action:

- Seed Demo Data button on the Project Middle Layer admin surface

Expected result:

- Marketplace, plugin, extension, and external agent demo entities are available
- Role profiles for phase10-platform-operator and phase10-platform-reviewer exist

## 4. Execute Core Operator Checks

Run these flows in order:

1. Compile a semantic payload
2. Review alerts and lineage
3. Run cross-platform sync
4. Validate BTIF+ export/validation path
5. Confirm plugin and extension operations

## 5. Confirm Health Signals

Validate dashboard indicators:

- Health score renders and trends are visible
- Drift and stability trend sparklines load
- Recent alerts and snapshots display without errors

## 6. Validate Control Behavior

Confirm UX/operator controls:

- Last section restore works on reload
- Density toggle persists
- Shortcuts rail state persists
- Capability-gated actions reject unauthorized users

## 7. Troubleshooting Fast Path

If actions fail:

- Check capability mapping and strict permission mode
- Review server logs and semantic audit entries
- Re-run seed command and reload admin page
- Verify database migration state and environment profile settings

## 8. Day-1 Operator Routine

- Review semantic health and alerts
- Triage recommendations and lineage issues
- Run required sync/orchestration jobs
- Record notable semantic changes through governed paths

## Related References

- [Project Middle Layer Platform Release Bulletin](../architecture/project_middle_layer_platform_release_bulletin.md)
- [Project Middle Layer Semantic OS Overview](../architecture/project_middle_layer_semantic_os_overview.md)
- [Project Middle Layer Developer Onboarding Guide](project_middle_layer_developer_onboarding_guide.md)
- [Environment Profiles](environment_profiles.md)
