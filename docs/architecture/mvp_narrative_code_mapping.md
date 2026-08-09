# MVP Narrative → Code Mapping

## Purpose

This document binds the canonical MVP narrative to the concrete Grassroots implementation surfaces that already exist in the repository. It is intended to keep product narrative, backend services, frontend panels, and governance contracts synchronized.

## Unified Blueprint

This blueprint is the governed next step for the repository: it explicitly ties each narrative phase to both GUI panel surfaces and backend micro-template runtime behavior so the platform does not drift between narrative intent and code execution.

### Panel Surface Mapping

| Narrative phase | GUI panel surface | Contract |
| --- | --- | --- |
| Idea | frontend_homepage/src/presentation/IspeIdeaScreen.jsx | Present the minimal entry state and preserve friction-free intent capture. |
| Seed | frontend_homepage/src/presentation/LfoExpansionPanel.jsx | Expose the seed thesis promotion path and preserve deterministic continuity. |
| Project | frontend_homepage/src/presentation/SopWorkflowScaffoldPanel.jsx | Render workflow, SOP, and timeline scaffolding with explicit semantic backing. |
| MVP | frontend_homepage/src/presentation/PublishingLayerHooksPanel.jsx | Publish investor and product-usage identities from deterministic project state. |

### Backend Micro-Template Mapping

| Narrative phase | Backend runtime contract | Row contract |
| --- | --- | --- |
| Idea | project_middle_layer/api/views.py and project_middle_layer/services.py | 4 subject-level entries |
| Seed | project_middle_layer/services.py | 16 branch-level promotion rows |
| Project | project_middle_layer/lfo_engine.py and project_middle_layer/services.py | 64 industry-level scaffolding rows |
| MVP | project_middle_layer/api/views.py | 256 sub-industry rows when runtime data is present |

### Governance Rules

- GUI semantics must remain explicit at each panel boundary.
- Backend row-count contracts must be enforced deterministically.
- Inheritance must follow the declared chain: 4 → 16 → 64 → 256.
- Frontend fallback may resolve 64 rows, while backend runtime resolves 256 rows when present.

## Phase Mapping

| Narrative phase | Primary implementation surface | Notes |
| --- | --- | --- |
| Idea | project_middle_layer/api/views.py, frontend_homepage/src/presentation/IspeIdeaScreen.jsx | Minimal entry and intent capture |
| Seed | project_middle_layer/services.py, project_middle_layer/api/views.py | Thesis formation and deterministic promotion |
| Project | project_middle_layer/lfo_engine.py, project_middle_layer/services.py, project_middle_layer/versioning.py | LFO, timeline, workflows, SOPs, and GUI endpoint |
| MVP | project_middle_layer/api/views.py, frontend_homepage/src/presentation/PublishingLayerHooksPanel.jsx | Investor and product-usage publication outputs |

## Deterministic Backbone

- Four-surface LFO: project_middle_layer/lfo_engine.py
- Inheritance map: platform_semantic/catalogs/macro_map.json
- Timeline runtime: project_middle_layer/services.py
- Unified intelligence envelope: project_middle_layer/lfo_engine.py and project_middle_layer/services.py
- Governance: workflow/meta/mvp_acceptance_manifest.json and scripts/operations/validate_mvp_acceptance_manifest.py

## Governance Contracts

- AC-IDEA-001 / AC-IDEA-002
- AC-SEED-001 / AC-SEED-002
- AC-PROJECT-001 through AC-PROJECT-007
- AC-MVP-001 through AC-MVP-003
- AC-INV-001 through AC-INV-003

## Validation

The repository already contains:

- CI gate: .github/workflows/mvp-acceptance-gate.yml
- Validator: scripts/operations/validate_mvp_acceptance_manifest.py
- Regression expectations: workflow/meta/mvp_acceptance_manifest.json
