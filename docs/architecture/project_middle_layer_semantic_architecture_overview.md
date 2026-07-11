# Project Middle Layer Semantic Architecture Overview

## Purpose

Project Middle Layer is the deterministic semantic control plane for project identity, semantic quality, governance, orchestration, and platform interoperability.

It transforms structured project intent into stable semantic state through reproducible compile, analysis, and governance pipelines.

## Architectural Principles

- Deterministic first: identical inputs produce predictable semantic outputs.
- Explicit structure over inference: strong schema, typed payloads, and validated transitions.
- Multi-surface parity: admin UI, API, and CLI expose equivalent core operations.
- Governance by default: audit, versioning, permissions, and change control are first-class.
- Platform extensibility: plugins, extensions, marketplace, external agents, and gateway support controlled expansion.

## Top-Level Layers

## Layer 1: Input and Compile

Primary components:

- Compile services and payload scaffold engines.
- Schema normalization and validation.
- Identity URI, branch resolution, and specialized path generation.

Outputs:

- Identity payload.
- Semantic tree.
- Drift, confidence, and stability primitives.

## Layer 2: Semantic Intelligence

Primary components:

- Evolution snapshots.
- Lineage records.
- Alert generation.
- Recommendations and insights.
- Analytics snapshots and trend points.

Outputs:

- Semantic health metrics.
- Actionable operator recommendations.
- Historical semantic trajectory.

## Layer 3: Governance and Change Control

Primary components:

- Roles, user profiles, and permissions.
- Edit sessions and change requests.
- Version commit/checkout.
- Semantic merge and audit logs.

Outputs:

- Controlled write access.
- Traceable semantic state transitions.
- Reviewable and restorable semantic history.

## Layer 4: Orchestration and Integration

Primary components:

- Pipelines and schedules.
- Webhooks and inbound/outbound integrations.
- Search and dashboard surfaces.

Outputs:

- Automatable semantic operations.
- Event-driven platform coordination.
- Operational observability.

## Layer 5: Distribution and Platformization

Primary components:

- Replication, federation, sharding, sync.
- Distributed agents and cache controls.
- Marketplace, plugins, extensions.
- API gateway and BTIF+ interoperability.
- External agent registration and sandbox execution.
- Cross-platform sync with conflict reporting.

Outputs:

- Scalable multi-node semantic operations.
- Controlled ecosystem extension model.
- Platform-to-platform semantic data exchange.

## Surface Map

## Admin Surface

- Primary command center for semantic operators.
- Project-level and platform-level control panels.
- Visual health, alert, recommendation, lineage, and platformization pages.

## API Surface

- DRF endpoints for compile, governance, orchestration, distribution, and platformization actions.
- Capability-aware access checks and audit logging.

## CLI Surface

- Command-oriented operation for automation and scripted workflows.
- Mirrors API/admin operations for deterministic operations in CI and ops scripts.

## Data Model Domains

Core domains include:

- Project identity and evolution.
- Semantic intelligence artifacts (alerts, lineage, analytics, agent runs).
- Governance entities (roles, permissions, change requests, audit logs, versions).
- Orchestration entities (pipelines, schedules, webhooks, integrations).
- Distribution entities (replication configs, federation peers, shards, sync logs).
- Platformization entities (marketplace, plugins, extensions, external agents, cross-sync logs).

## Flow Overview

1. Operator or client submits compile payload.
2. Compile engine generates deterministic semantic payload.
3. Snapshot, lineage, and alerts are persisted.
4. Analytics and recommendations are available for operators.
5. Governance and versioning control subsequent changes.
6. Pipelines/schedules/webhooks propagate operations.
7. Platformization layer enables extension and interoperability.

## Security and Permissions

- Strict permission mode can be enabled by environment.
- Capability checks guard mutating operations.
- Superuser and staff compatibility is preserved for admin control.
- Audit logs capture semantic action and source context.

## Interoperability

- Gateway provides route map, schema introspection, and dispatch semantics.
- BTIF+ provides semantic exchange envelope and validation contract.
- Cross-platform sync encapsulates interoperability run status and conflicts.

## Operator Model

Typical operator loops:

- Compile -> Observe drift/confidence -> Apply recommendation -> Version commit.
- Review alerts -> Trigger pipeline/schedule -> Verify in dashboard.
- Validate extension/plugin changes in controlled environments.
- Execute cross-platform sync and review conflict reports.

## Architectural References

- docs/architecture/project_middle_layer_platform_release_notes_phase1_to_phase10.md
- docs/operations/project_middle_layer_phase10_roles.md
- docs/operations/environment_profiles.md
