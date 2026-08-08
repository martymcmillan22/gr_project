# Intro to Django

## Project Middle Layer Announcement

Project Middle Layer is now complete as the semantic operating system for GrassRoots: a deterministic, capability-gated platform that unifies compile, identity-aware routing, lineage, governance, orchestration, and external interoperability into one production-ready control plane.

With plugins, extensions, marketplace packaging, BTIF+ export and validation, federation, gateway integration, and external agents fully in place, the platform is built for safe scale, auditable operations, and long-term semantic evolution.

![CPINDCNO Constitutional Guardrail](https://img.shields.io/badge/CPINDCNO-Constitutional_Guardrail_PASS-2ea44f?style=for-the-badge)

This is the code for the *O'Reilly Video* - **Intro to Django** presented by Arianne Dee.

You can download a PDF of the slides [here](https://drive.google.com/file/d/1F-FDjBJnjrhnB7ulM3DJuro_T-5M07r-/view?usp=sharing).

## AI Workflow Directive

This repository uses a deterministic AI workflow for UI and semantic work.

See [GRASSROOTS_AI_WORKFLOW.md](GRASSROOTS_AI_WORKFLOW.md) for the Penpot to MDX to React to MLAS BTIF directive that all AI assistants should follow.

## BaseTrue Master Architecture Document

This document unifies all major subsystems of the BaseTrue / GRASSROOTS platform into a single deterministic macro-architecture. It is designed as the Continuity Bridge reference for development, VS Code AI alignment, and long-term platform evolution.

---

## 1. Purpose

BaseTrue is a deterministic multi-layer semantic platform. Every subsystem (BTIF, BTPE, PIP, Polish, Task Manager, Project Middle Layer, VA, POVs, UI, Platform Core) forms one layer of a single pipeline:

Idea -> Seed -> Project -> Identity -> Narrative -> Delivery

This document defines how each layer fits together.

---

## 2. Semantic Entry Points (home/ index)

The platform begins at home/, which routes users into one of three semantic domains:

### Public Center

- Public ideas, seeds, projects
- Public POVs
- Public storytelling

### Personal Domain

- Private ideas, seeds, projects
- Personal POVs
- Personal storytelling

### Enterprise Center

- Enterprise ideas, seeds, projects
- Enterprise workflows
- Enterprise POVs
- Enterprise storytelling dashboards

These three domains share the same deterministic pipeline but operate with different scopes and permissions.

---

## 3. Semantic Foundation

### BTIF

Canonical ontology:

- 4 subjects
- 16 branches
- 64 industries
- 256 sub-industries
- 12 temporal slots

### domain/

Django models implementing BTIF ontology.

### platform_semantic/

Semantic bundles, presets, catalogs.

Canonical industry-sector ontology: platform_semantic/catalogs/macro_map.json.

### platform_reference/

GICS, NAICS, MLAS, CCCP, DCHD reference datasets.

This layer is the source of truth for meaning, structure, and classification.

---

## 4. Deterministic Pattern Engine (BTPE)

### basetrue_engine/

Implements BTPE:

- Rule selection
- Constraint validation
- Hierarchy expansion (SVEM -> CCCP -> DCHD)
- Narrative scaffolding

### platform_runtime/

Execution layer, pipelines, schedulers.

BTPE is the behavioral brain of the platform.

---

## 5. Workflow Layer (PIP + Polish + Task Manager)

This layer governs Idea -> Seed -> Project.

### peringram/

SRL maps, convection cycle, industry hierarchy.

### workflow/

Workflow routing and deterministic movement.

### polish/

Early-stage refinement, seed formation.

### Task Manager

Assignment engine for:

- Idea refinement
- Seed formation
- Seed -> Project promotion

This is Governance Tier 1.

---

## 6. Project Governance Layer (Project Middle Layer)

### project_middle_layer/

Governs Project -> Identity -> Narrative -> Delivery:

- Semantic pipelines
- Schedules
- Drift detection
- Analytics
- Versioning
- Agents

This is Governance Tier 2.

---

## 7. Virtual Assistant (VA)

The VA is the semantic orchestrator of both governance tiers.

### VA responsibilities

- Interpret user intent
- Read semantic analytics
- Provide nudges and reminders
- Strengthen narrative intent
- Trigger pipelines, schedules, agents
- Keep users on track across all phases

The VA is a separate app that uses the Middle Layer as its semantic engine.

---

## 8. Narrative + Perspective Layer (POVs + Storytelling Engine)

### povs/

Public, personal, enterprise perspectives.

### storytelling-engine/

Narrative scaffolding and story views.

### storytelling_dashboard/

Enterprise storytelling analytics.

This layer provides semantic lenses and narrative surfaces.

---

## 9. UI Delivery Layer (4-Block UI)

Every phase uses the same deterministic UI scaffold:

- List
- Details
- Howto
- Present

Implemented across:

- ui/
- ui_apps/
- ui_template_library/
- home/ (index)
- homepage/ (test)
- frontend_homepage/ (legacy)

---

## 10. Platform Infrastructure (Platform Core Split)

Platform Core is split into four apps:

### platform_semantic/

Semantic bundles, presets, catalogs.

### platform_quadrant/

Quadrant resolver, domain routing, overlays.

### platform_billing/

Billing, invoices, diagnostics.

### platform_reference/

Reference datasets and sync.

These provide shared services and semantic infrastructure.

---

## 11. Deterministic Pipeline (Master Spine)

The entire platform follows one deterministic pipeline:

Idea -> Seed -> Project -> Identity -> Narrative -> Delivery

- Governance Tier 1: Polish + Task Manager
- Governance Tier 2: Project Middle Layer
- Orchestrator: VA
- Entry Points: Public, Personal, Enterprise
- Foundation: BTIF
- Compiler: BTPE
- Delivery: 4-Block UI + POVs + Storytelling Engine

---

## 12. Cross-Layer Integration Rules

1. All features must map to BTIF ontology.
2. All workflows route through project_middle_layer for state and governance.
3. All UI surfaces consume Middle Layer + POVs, not raw models.
4. Platform Core provides shared services only.
5. Documentation must narrate the pipeline in deterministic order.

---

## 13. Repository Mapping

### Semantic Foundation

- BTIF/
- domain/
- platform_semantic/

### Pattern Engine

- basetrue_engine/
- platform_reference/

### Workflow

- peringram/
- workflow/
- polish/
- Task Manager

### Governance

- project_middle_layer/
- VA/

### Narrative

- povs/
- storytelling-engine/
- storytelling_dashboard/

### UI

- home/
- ui/
- ui_apps/
- ui_template_library/

### Infrastructure

- platform_semantic/
- platform_quadrant/
- platform_billing/
- platform_reference/

### Documentation

- README.md
- docs/
- GRASSROOTS_AI_WORKFLOW.md

---

## 14. Final Summary

BaseTrue is a deterministic semantic platform with a unified pipeline and a multi-layer architecture. This document defines the Continuity Bridge that ties all subsystems together and provides the macro perspective required for VS Code AI alignment and long-term platform evolution.

### Current State vs Target State (Continuity Bridge Alignment)

#### 1. Semantic Foundation

- Current state:
- `BTIF/` and `domain/` exist and are wired.
- No standalone `platform_semantic/` or `platform_reference/` apps; semantic and reference logic live inside `platform_core/` and related data modules.
- Target state:
- Introduce `platform_semantic/` and `platform_reference/` as dedicated apps for bundles and reference datasets.
- Gradually migrate semantic and reference responsibilities out of `platform_core/` into these apps.

#### 2. Pattern Engine (BTPE)

- Current state:
- Engine folder is named `baseture_engine/` (not `basetrue_engine/`).
- No `platform_runtime/` top-level app; runtime behavior is handled inside existing apps and `platform_core/`.
- Target state:
- Normalize naming: either rename folder to `basetrue_engine/` or update architecture to `baseture_engine/` consistently.
- Define `platform_runtime/` as the future home for pipelines, schedulers, and execution logic.

#### 3. Workflow Layer (PIP + Polish + Task Manager)

- Current state:
- `peringram/`, `workflow/`, and `polish/` exist and are active.
- Task Manager logic lives under `task_manager/` as a nested subsystem, not a standalone app.
- Target state:
- Clarify in architecture that Task Manager is currently implemented under `task_manager/`.
- Evolve Task Manager + Polish into the explicit governance layer for Idea -> Seed -> Project, with VA orchestration.

#### 4. Governance + VA

- Current state:
- `project_middle_layer/` exists, is installed, and governs projects.
- `VA_default_image/` exists as assets only; no standalone `va` Django app or URL include yet.
- Target state:
- Keep Project Middle Layer as Governance Tier 2 for Project -> Identity -> Narrative -> Delivery.
- Implement VA as a real Django app (for example `va/`), register it in `settings.py`, and wire URLs so it can orchestrate both governance tiers.

#### 5. Platform Core Split

- Current state:
- `platform_core/` is a monolithic, registered Django app.
- All platform services, references, and bundles live inside `platform_core/`.
- System checks pass cleanly with this monolith.
- Target state:
- Gradually refactor `platform_core/` into four apps: `platform_semantic/`, `platform_quadrant/`, `platform_billing/`, `platform_reference/`.
- Maintain internal consistency and avoid circular dependencies during the split.

#### 6. Home as True Index (Public / Personal / Enterprise)

- Current state:
- Root routing points to `home/` and index template.
- Index UI surfaces Public and Personal entry points only.
- No Enterprise entry button or route is exposed on the home index yet.
- Target state:
- Keep `home/` as the canonical index.
- Add an Enterprise entry surface (button/link + route) to match the three-domain architecture: Public Center, Personal Domain, Enterprise Center.

### Continuity Bridge Alignment Checklist (Normalized)

Statuses: Complete, In Progress, Planned

Machine-readable tracker:
- [workflow/meta/continuity_bridge_alignment.json](workflow/meta/continuity_bridge_alignment.json)

#### 1. Semantic Foundation

- `BTIF/` - **Complete**
- `domain/` - **Complete**
- `platform_semantic/` - **In Progress**
- `platform_reference/` - **In Progress**
- Consolidate semantic and reference logic out of `platform_core/` - **Planned**

#### 2. Pattern Engine (BTPE)

- Normalize naming (`basetrue_engine` vs `baseture_engine`) - **In Progress**
- Create `platform_runtime/` for pipelines and schedulers - **Planned**

#### 3. Workflow Layer (Idea -> Seed -> Project)

- `peringram/` - **Complete**
- `workflow/` - **Complete**
- `polish/` - **Complete**
- Task Manager under `task_manager/` - **Complete**
- Promote Polish and Task Manager to Governance Tier 1 - **In Progress**

#### 4. Governance Layer (Project -> Identity -> Narrative -> Delivery)

- `project_middle_layer/` - **Complete**
- VA orchestration (conceptual) - **Complete**
- VA Django app implementation - **Planned**
- VA URL routing - **Planned**

#### 5. Platform Core Split

- Current monolith: `platform_core/` - **Complete**
- `platform_semantic/` - **In Progress**
- `platform_quadrant/` - **In Progress**
- `platform_billing/` - **In Progress**
- `platform_reference/` - **In Progress**
- Migration strategy - **In Progress**

#### 6. Home as True Index (Public / Personal / Enterprise)

- `home/` as index - **Complete**
- Public entry - **Complete**
- Personal entry - **Complete**
- Enterprise entry - **Planned**
- Enterprise routing - **Planned**

#### 7. Narrative + POV Layer

- `povs/` - **Complete**
- `storytelling-engine/` - **Complete**
- `storytelling_dashboard/` - **Complete**
- Enterprise POVs - **Planned**

#### 8. UI Delivery Layer (4-Block UI)

- `ui/` - **Complete**
- `ui_apps/` - **Complete**
- `ui_template_library/` - **Complete**
- `home/` - **Complete**
- Add Enterprise UI surfaces - **Planned**

#### 9. Documentation Layer

- `README.md` - **Complete**
- Master Architecture Document - **Complete**
- Continuity Bridge Alignment - **Complete**
- Add migration timeline - **Planned**

### BaseTrue Continuity Bridge - Migration Timeline (Deterministic Roadmap)

All phases map directly to the JSON tracker statuses: Complete -> In Progress -> Planned.

#### Phase 0 - Foundation Locked (Complete)

These items are already stable and form the base of the migration timeline.

- BTIF - Complete
- domain - Complete
- project_middle_layer - Complete
- povs - Complete
- storytelling-engine - Complete
- ui - Complete
- home/ index routing - Complete
- Master Architecture Document - Complete
- Continuity Bridge Alignment - Complete
- JSON tracker - Complete

Outcome:
The semantic foundation, governance tier 2, narrative layer, UI layer, and documentation spine are stable.

#### Phase 1 - Naming and Early Governance (In Progress)

These items are already underway and should be completed before structural migrations.

1. Normalize BTPE naming
- basetrue_engine vs baseture_engine -> In Progress
2. Promote Polish and Task Manager to Governance Tier 1
- Idea -> Seed -> Project governance -> In Progress
3. Platform Core migration strategy
- Planning the split -> In Progress

Outcome:
Early-stage governance becomes deterministic, and naming drift is eliminated.

#### Phase 2 - Enterprise Entry (Planned -> In Progress)

This is the next major architectural milestone.

Enterprise entry tasks:

- Add Enterprise entry button to home/
- Add Enterprise routing
- Add Enterprise POVs
- Add Enterprise UI surfaces

All currently Planned in JSON.

Outcome:
BaseTrue becomes a three-domain semantic platform: Public -> Personal -> Enterprise.

#### Phase 3 - VA Implementation (Planned -> In Progress)

This is the most important functional migration.

VA tasks:

- Create VA Django app
- Register VA in settings.py
- Add VA URLs
- Add VA views
- Connect VA to Governance Tier 1
- Connect VA to Governance Tier 2

All currently Planned.

Outcome:
VA becomes the orchestrator of the entire deterministic pipeline.

#### Phase 4 - Platform Core Split (In Progress)

This is the largest structural migration.

Split tasks:

- Create platform_semantic/
- Create platform_quadrant/
- Create platform_billing/
- Create platform_reference/
- Move logic out of platform_core/
- Remove monolithic dependencies
- Validate Django app registration
- Validate imports and routing

All currently Planned.

Outcome:
Platform Core becomes modular, deterministic, and enterprise-ready.

#### Phase 5 - Runtime Layer (Planned)

This is the execution backbone.

Runtime tasks:

- Create platform_runtime/
- Move pipelines
- Move schedulers
- Move background tasks
- Move semantic jobs

Currently Planned.

Outcome:
BaseTrue gains a dedicated execution layer for semantic pipelines.

#### Phase 6 - Migration Timeline Publication (Planned)

This is the final documentation step.

Documentation tasks:

- Add migration timeline to README
- Add migration timeline to docs/
- Add migration timeline to JSON tracker
- Add migration timeline to GRASSROOTS_AI_WORKFLOW.md

Currently Planned.

Outcome:
Your Continuity Bridge becomes fully versioned and self-maintaining.

#### Full Timeline Summary (JSON -> Roadmap)

- Phase 0: Foundation - Complete
- Phase 1: Naming and Governance Tier 1 - In Progress
- Phase 2: Enterprise Entry - Planned -> In Progress
- Phase 3: VA Implementation - Planned -> In Progress
- Phase 4: Platform Core Split - In Progress
- Phase 5: Runtime Layer - Planned
- Phase 6: Timeline Publication - Planned

### Enterprise Entry Point - Deterministic Design (BaseTrue Continuity Bridge)

Public -> Personal -> Enterprise

#### Takeaway

The Enterprise Entry Point is a third semantic domain on the home index, parallel to Public Center and Personal Domain, and governed by the same deterministic pipeline:

Idea -> Seed -> Project -> Identity -> Narrative -> Delivery

Enterprise gets its own:

- entry button
- route
- Django app surface
- POV set
- storytelling dashboard
- governance rules
- VA orchestration hooks

This makes BaseTrue a three-pillar semantic platform.

#### 1. Enterprise Entry Button (home/index.html)

Placed alongside Public and Personal.

- Button label: Enterprise Center
- Button description: Structured workflows, enterprise seeds, enterprise projects, and enterprise storytelling dashboards.
- Route: /enterprise/

#### 2. Enterprise Django App Structure

- Folder: enterprise/
- Subfolders:
- views/
- templates/enterprise/
- urls.py
- povs/enterprise/
- workflows/enterprise/
- storytelling_dashboard/enterprise/
- AppConfig: EnterpriseConfig
- Installed apps: add enterprise to settings.py

#### 3. Enterprise URL Routing

home/urls.py add:

- path("enterprise/", include("enterprise.urls"))

enterprise/urls.py routes:

- /enterprise/ideas/
- /enterprise/seeds/
- /enterprise/projects/
- /enterprise/story/
- /enterprise/pov/
- /enterprise/dashboard/

#### 4. Enterprise POV Set

- Enterprise Strategy POV
- Enterprise Operations POV
- Enterprise Narrative POV
- Enterprise Delivery POV

These POVs interpret enterprise projects through:

- strategic alignment
- operational feasibility
- narrative strength
- delivery readiness

#### 5. Enterprise Storytelling Dashboard

Enterprise storytelling is more analytical:

- timelines
- drift detection
- semantic alignment
- delivery readiness
- narrative strength
- enterprise bundles
- enterprise BTIF overlays

Dashboard route: /enterprise/dashboard/

#### 6. Enterprise Governance Rules

Enterprise follows the same deterministic pipeline:

Idea -> Seed -> Project -> Identity -> Narrative -> Delivery

With enterprise-specific governance:

- enterprise idea intake
- enterprise seed validation
- enterprise project promotion
- enterprise identity alignment
- enterprise narrative dashboards
- enterprise delivery readiness

Governance Tier 1 (Polish + Task Manager) handles:

- enterprise ideas
- enterprise seeds
- enterprise seed -> project promotion

Governance Tier 2 (Project Middle Layer) handles:

- enterprise projects
- enterprise identity
- enterprise narrative
- enterprise delivery

#### 7. VA Orchestration for Enterprise

VA acts as semantic conductor for enterprise:

- enterprise idea refinement
- enterprise seed formation
- enterprise project governance
- enterprise narrative strengthening
- enterprise delivery readiness

VA routes enterprise tasks through:

- Governance Tier 1
- Governance Tier 2
- enterprise POVs
- enterprise storytelling dashboards

#### 8. Enterprise UI Surfaces (4-Block UI)

Enterprise uses the same deterministic UI scaffold:

- List
- Details
- Howto
- Present

Enterprise surfaces:

- enterprise ideas
- enterprise seeds
- enterprise projects
- enterprise POVs
- enterprise storytelling dashboards

#### 9. Enterprise Entry Integration Checklist

- Add Enterprise button to home/index.html
- Create enterprise/ app
- Add enterprise URLs
- Add enterprise POVs
- Add enterprise storytelling dashboard
- Add enterprise workflows
- Add enterprise governance hooks
- Add enterprise UI surfaces
- Add enterprise routing to VA
- Update JSON tracker statuses

### VA Dual Governance - Deterministic Semantic Architecture

#### Takeaway

The VA becomes a two-tier semantic orchestrator.

- governs early-stage movement: Idea -> Seed -> Project
- governs late-stage evolution: Project -> Identity -> Narrative -> Delivery
- routes all actions through deterministic pipelines
- strengthens narrative intent
- keeps users on track across Public, Personal, and Enterprise domains

This is the semantic brain of BaseTrue.

#### 1. VA Django App Structure (New App: va/)

- Folder: va/
- Subfolders:
- views/
- services/
- governance/
- routes/
- templates/va/
- analytics/
- intent/
- AppConfig: VAConfig
- Installed apps: add va to settings.py
- Purpose: semantic conductor for both governance tiers

#### 2. VA Routing (urls.py)

home/urls.py add:

- path("va/", include("va.urls"))

va/urls.py routes:

- /va/intent/
- /va/idea/
- /va/seed/
- /va/project/
- /va/identity/
- /va/narrative/
- /va/delivery/
- /va/enterprise/

These routes map directly to deterministic pipeline phases.

#### 3. VA Intent Engine (Semantic Interpreter)

The VA must interpret user intent across Public, Personal, and Enterprise.

Intent categories:

- Idea creation
- Seed refinement
- Seed -> Project promotion
- Project governance
- Identity alignment
- Narrative strengthening
- Delivery readiness
- Enterprise workflows

Intent engine responsibilities:

- classify user action
- map to deterministic pipeline
- route to correct governance tier
- apply POV lens
- trigger storytelling updates
- maintain semantic continuity

#### 4. Governance Tier 1 (Polish + Task Manager)

Idea -> Seed -> Project

VA orchestrates:

- idea refinement
- seed formation
- seed validation
- seed -> project promotion
- assignment workflows
- staff workflows
- convection cycles
- SRL maps

Integration paths:

- VA -> Polish
- VA -> Task Manager
- VA -> PIP

#### 5. Governance Tier 2 (Project Middle Layer)

Project -> Identity -> Narrative -> Delivery

VA orchestrates:

- project state transitions
- drift detection
- schedules
- semantic versioning
- narrative alignment
- POV alignment
- delivery readiness
- enterprise routing

Integration paths:

- VA -> Project Middle Layer
- VA -> Storytelling Engine
- VA -> POVs

#### 6. VA Enterprise Governance

Enterprise VA routing covers:

- enterprise idea intake
- enterprise seed formation
- enterprise seed -> project promotion
- enterprise project governance
- enterprise identity alignment
- enterprise narrative dashboards
- enterprise delivery readiness

Enterprise integrations:

- VA -> Enterprise POVs
- VA -> Enterprise Storytelling Dashboard

#### 7. VA Analytics Layer

The VA reads:

- semantic drift
- narrative strength
- delivery readiness
- project health
- seed viability
- idea clarity
- enterprise alignment

This analytics layer powers VA nudges and guidance.

#### 8. VA UI Surfaces (Optional)

Possible VA surfaces:

- VA dashboard
- VA intent history
- VA semantic nudges
- VA governance timeline
- VA enterprise insights

Surface path: templates/va/

#### 9. VA Dual Governance Integration Checklist

- Create va/ app
- Add VA to settings.py
- Add VA URLs
- Add VA views
- Add VA intent engine
- Add VA governance tier 1 routing
- Add VA governance tier 2 routing
- Add VA enterprise routing
- Add VA analytics layer
- Add VA POV integration
- Add VA storytelling integration
- Update JSON tracker statuses

## Environment Recommendations

Recommended baseline values for local, staging, and production are documented in:

- [docs/operations/environment_profiles.md](docs/operations/environment_profiles.md)

For Project Middle Layer rollout, the key toggle is:

- `PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=false` in local dev
- `PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=true` in staging
- `PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=true` in production

## Workflow Platform (Canonical)

The canonical workflow command center is under [workflow](workflow).

Core categories:
1. [workflow/database_design/mermaid_erds](workflow/database_design/mermaid_erds)
2. [workflow/logic_design/mermaid_sequences](workflow/logic_design/mermaid_sequences)
3. [workflow/ui_templates/penpot_templates](workflow/ui_templates/penpot_templates)
4. [workflow/ui_components/penpot_components](workflow/ui_components/penpot_components)

Workflow engine entrypoint:
- [workflow/cli.py](workflow/cli.py)

Workflow docs:
- [workflow/README.md](workflow/README.md)
- [workflow/meta/docs/ARCHITECTURE_OVERVIEW.md](workflow/meta/docs/ARCHITECTURE_OVERVIEW.md)
- [workflow/meta/docs/SEMANTIC_OVERVIEW.md](workflow/meta/docs/SEMANTIC_OVERVIEW.md)
- [workflow/meta/docs/SEMANTIC_DRIFT_OVERVIEW.md](workflow/meta/docs/SEMANTIC_DRIFT_OVERVIEW.md)
- [workflow/meta/docs/SEMANTIC_INFERENCE_OVERVIEW.md](workflow/meta/docs/SEMANTIC_INFERENCE_OVERVIEW.md)
- [workflow/meta/ai_hints.json](workflow/meta/ai_hints.json)
- [workflow/meta/ai_navigation.json](workflow/meta/ai_navigation.json)
- [workflow/meta/semantic_context.json](workflow/meta/semantic_context.json)
- [workflow/meta/docs/RELEASE_OVERVIEW.md](workflow/meta/docs/RELEASE_OVERVIEW.md)
- [workflow/meta/docs/VERSIONING_GUIDE.md](workflow/meta/docs/VERSIONING_GUIDE.md)
- [workflow/meta/version.json](workflow/meta/version.json)
- [workflow/meta/governance_policy.json](workflow/meta/governance_policy.json)
- [workflow/meta/docs/SEMANTIC_EVOLUTION_OVERVIEW.md](workflow/meta/docs/SEMANTIC_EVOLUTION_OVERVIEW.md)
- [workflow/meta/ai_evolution.json](workflow/meta/ai_evolution.json)
- [workflow/meta/docs/FEATURE_EXPANSION_OVERVIEW.md](workflow/meta/docs/FEATURE_EXPANSION_OVERVIEW.md)
- [workflow/meta/ai_expansion.json](workflow/meta/ai_expansion.json)
- [workflow/meta/docs/SEMANTIC_REFACTORING_OVERVIEW.md](workflow/meta/docs/SEMANTIC_REFACTORING_OVERVIEW.md)
- [workflow/meta/ai_refactor.json](workflow/meta/ai_refactor.json)
- [workflow/meta/docs/SEMANTIC_IMPROVEMENT_CYCLE_OVERVIEW.md](workflow/meta/docs/SEMANTIC_IMPROVEMENT_CYCLE_OVERVIEW.md)
- [workflow/meta/ai_cycle.json](workflow/meta/ai_cycle.json)

Common commands:
- python3 workflow/cli.py new-feature --name "Feature Name" --mlas-tier "Tier" --btif-classification "Class" --semantic-intent "Intent" --semantic-tags tag1 tag2
- python3 workflow/cli.py validate-suite
- python3 workflow/cli.py classify
- python3 workflow/cli.py semantic-check
- python3 workflow/cli.py sync --feature <slug>
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py semantic-drift
- python3 workflow/cli.py semantic-infer
- python3 workflow/cli.py semantic-resolve
- python3 workflow/cli.py semantic-health
- python3 workflow/cli.py semantic-scorecard
- python3 workflow/cli.py semantic-strategy-report
- python3 workflow/cli.py semantic-health --profile quarterly
- python3 workflow/cli.py improve-all --profile quarterly
- python3 workflow/cli.py semantic-scorecard --profile quarterly --min-confidence 0.85
- python3 workflow/cli.py semantic-strategy-report --profile quarterly --period YYYY-QN --quarterly-alignment
- python3 workflow/cli.py semantic-health --profile annual
- python3 workflow/cli.py semantic-drift-forecast --profile annual --horizon-months 12
- python3 workflow/cli.py improve-all --profile annual
- python3 workflow/cli.py semantic-scorecard --profile annual --min-confidence 0.85
- python3 workflow/cli.py semantic-strategy-report --profile annual --period YYYY
- python3 workflow/cli.py ai-context
- python3 workflow/cli.py ai-export
- python3 workflow/cli.py ai-new-feature --name "Feature Name"
- python3 workflow/cli.py version
- python3 workflow/cli.py bump-version --part patch
- python3 workflow/cli.py release --bump patch [--approve-semantic-changes]
- python3 workflow/cli.py release-notes
- python3 workflow/cli.py evolve-feature --feature <slug>
- python3 workflow/cli.py evolve-all
- python3 workflow/cli.py evolve-preview
- python3 workflow/cli.py expand [--target <slug>]
- python3 workflow/cli.py expand-all
- python3 workflow/cli.py expand-preview
- python3 workflow/cli.py refactor-feature --feature <slug>
- python3 workflow/cli.py refactor-all
- python3 workflow/cli.py refactor-preview
- python3 workflow/cli.py improve-feature --feature <slug>
- python3 workflow/cli.py improve-all
- python3 workflow/cli.py improve-preview

## AWS Deployment Docs

AWS planning and execution docs are organized under [docs/operations/aws](docs/operations/aws).

Primary entry point:
- [docs/operations/aws/README.md](docs/operations/aws/README.md)

Suggested reading order:
1. [AWS Deployment Recommendation](docs/operations/aws/aws_deployment_recommendation.md)
2. [AWS Implementation Plan](docs/operations/aws/aws_implementation_plan.md)
3. [AWS Staging Resource Checklist](docs/operations/aws/aws_staging_resource_checklist.md)
4. [AWS Staging Deployment Checklist](docs/operations/aws/aws_staging_deployment_checklist.md)

## Diagram Library

All Grassroots architecture and workflow diagrams are stored in [grassroots_diagrams](grassroots_diagrams).

These Mermaid files define the Penpot to MDX to React to MLAS BTIF pipeline and are used for onboarding, semantic reference, and VS Code AI tasks.

## Course setup

1. [Install Python 3.11](#1-install-python-311)
1. [Check that Python was installed properly](#2-make-sure-that-python-is-properly-installed)
1. [Choose an IDE](#3-choose-an-ide)
1. [Download the code](#4-download-the-course-files)
1. [Create a virtual environment](#5-create-a-virtual-environment)
1. [Install Django](#6-install-django)

## Set up instructions
Feel free to email me at
[basetruegrassroots@gmail.com](mailto:basetruegrassroots@gmail.com)
if you are having any problems getting set up for the course.

### 1. Install Python 3.11

This course uses Python 3.11, but Python 3.8 and higher should work.

The course uses Django 4.2,
so check which Python versions are compatible with 
Django 4.2 [here](https://docs.djangoproject.com/en/4.2/faq/install/#faq-python-version-support).

#### To install the latest version of Python:
1. Go to https://www.python.org/downloads/
1. Click the yellow button at the top to download the latest version of Python.

#### On Mac or Linux
Follow the prompts and install using the default settings.

#### On Windows
The default settings don't add Python to your PATH
so your computer doesn't know where to look for it when Python runs
(for some inexplicable reason).

##### If you're just installing Python now
Follow the instructions here: [Windows Python installer instructions](docs/install/WININSTALL.md)

##### If you've already installed Python with the default settings
Follow the instructions here: [Add Python to PATH variable in Windows](docs/install/WINSETPATH.md)

### 2. Make sure that Python is properly installed
1. Open the *PowerShell* application in Windows
   or *Terminal* on Mac or Linux

1. Type `python --version` and press enter
2. Type `python3 --version` and press enter
3. Type `py --version` and press enter

At least one of those commands should print
a Python version of 3.8 or higher
(whichever version you just installed).
If it doesn't, you have to follow instructions to
[add Python to your PATH variable](docs/install/WINSETPATH.md).

### 3. Choose an IDE
**PyCharm** or **VS Code** are recommended.

For Django development, I recommend using **PyCharm Professional Edition** (paid).
There is a 30-day free trial if you would like to try it out.

In the video I use the free **PyCharm Community Edition**, which is sufficient.

Download either version here: https://www.jetbrains.com/pycharm/download/

Install, open, and use the default settings.

### 4. Download the course files

#### If you know git:
Clone the repository.

#### If you don't know git:
1. Click the green "Code" button at the top-right of the page
2. Click "Download ZIP"
3. Unzip it and move the **intro-to-django-main** folder to a convenient location

### 5. Create a virtual environment
1. In your console, navigate to the project folder (if you open the project in PyCharm or VSCode, the Terminal pane should already be located there)
2. Using the python command from step 2, create a virtual environment
`python -m venv django_venv` or `python3 -m venv django_venv`
3. Activate your virtual environment
   - **Mac/Linux**: `source django_venv/bin/activate`
   - **PowerShell**: `django_venv\Scripts\Activate.ps1`

If you are new to virtual environments, please watch this 
[video lesson](https://learning.oreilly.com/videos/next-level-python/9780136904083/9780136904083-NLP1_01_03_03/)

### 6. Install Django
Once your virtual environment has been activated, install Django 3 using pip:
- `pip install django` to install the latest version of Django
  
**OR**
- `pip install "django>=4.2,<5"` to install the latest Django 4.2 version (once version 5+ is released)

## FAQs
### Can I use Python 2?

No. Django 3+, does not support Python 2 or Python < 3.6.

### PyCharm can't find Python 3

On a Mac:
- Go to **PyCharm** > **Preferences**

On a PC:
- Go to **File** > **Settings**

Once in Settings:
1. Go to **Project: intro-to-django** > **Project Interpreter**
1. Look for your Python version in the Project Interpreter dropdown
1. If it's not there, click **gear icon** > **Add...**
1. In the new window, select **System Interpreter** on the left, and then look for the Python version in the dropdown
1. If it's not there, click the **...** button and navigate to your Python location
    - To find where Python is located, [look in these directories](docs/install/PATH_LOCATIONS.md)
    - You may have to search the internet for where Python gets installed by default on your operating system

### How do I set up my IDE to use Django?
Here are some links to configure your Django project in the following IDEs
- [PyCharm Professional](docs/config/PyCharm_Pro.md)
  - My IDE of choice for working in Django
- [PyCharm Community](docs/config/PyCharm_Com.md)

- [VS Code](docs/config/VSCode.md)

---

## Django Trivia example project

### Local setup instructions

1. Navigate into the `trivia_site` folder
1. Create a virtual environment with Python 3.8+
1. Activate your virtual environment
1. `$ pip install --upgrade pip` to upgrade pip
1. `$ pip install -r requirements/local.txt` to install local requirements
1. `$ python manage.py migrate` to migrate your database
1. `$ python manage.py createsuperuser` and follow instructions
1. `$ python manage.py loaddata questions` to add seed data
1. `$ python manage.py runserver` to run the development server

### Production setup instructions

Live website at https://trivia-ariannedee.pythonanywhere.com/.

Hosted on Python Anywhere using Python 3.10 and MySQL 5.7.

To get a copy in production on your own server:

1. Set up a server environment with Python 3.8 or higher and a database (Postgres or MySQL preferred)
2. Fork this project or create a copy of the `trivia_site` folder in your own repository and clone into your sever
**Note**: The next few steps may differ depending on what kind of server/service you are using. Follow a Django setup tutorial if you can find one.
3. Create and activate a virtual environment if desired
4. Set the `DJANGO_SETTINGS_MODULE` environment variable to `trivia_project.settings.production`
   - `$ export DJANGO_SETTINGS_MODULE=trivia_project.settings.local` on Linux
   - On PythonAnywhere, edit the WSGI configuration file with `os.environ['DJANGO_SETTINGS_MODULE'] = 'trivia_project.settings.production'`
   - This makes sure running `manage.py` uses the right settings file
5. Configure the server to use WSGI (instead of `python manage.py runserver`)
   - Point to `trivia_project.wsgi.application` or configure a `wsgi.py` file on the server (follow tutorial instructions)
6. Set up your secrets in a `.env` file
   - Duplicate `.env.example` and save it as `.env`
   - Fill in the `DJANGO_SECRET_KEY` field with a random string of 50+ characters
   - Fill in the `DB_PASSWORD` field
   - Email fields are only used for the forgot password feature. If you want to get it working, the easiest is to create a new Gmail address and create an app password for it and use that for `EMAIL_PASSWORD`
7. Edit `trivia_site/trivia_project/settings/production.py`
   - Update `ALLOWED_HOSTS` to use your server address(es)
   - Edit your database settings (except password)
8. Edit `trivia_site/requirements/production.txt` to use the correct package for your database
   - Use a different `mysqlclient` if necessary, or `psycopg` or `psycopg2` if using Postgres (or other package if using a different DB)
   - This might be trial and error. You can pip install it, try to get it working, then update the requirements file with the pinned version
9. Install the requirements `$ pip install -r requirements/production.txt`
10. Run/reload the server and see if it works, troubleshoot if necessary
   - You may need to do more configuration to properly serve your static and media files. Look for a tutorial for your cloud provider or server type.
   - If you cannot serve media files from the same server, use Amazon S3
11. Migrate the database by running `python manage.py migrate`
12. If that works, commit any code changes you made.
13. `$ python manage.py createsuperuser` and follow instructions
14. `$ python manage.py loaddata questions` to add seed data
15. `$ python manage.py collectstatic` to collect the static files into `staticfiles/` (run this every time your static files change)

Please let me know if you have any suggestions/updates/questions about these instructions.

---

## Questions or comments?

Email me at  
[**basetruegrassroots@gmail.com**](mailto:basetruegrassroots@gmail.com) 
or submit an issue or pull request to this repository.

---

## BaseTrue Monthly Newsletter

The project now includes a monthly newsletter app at `/base-true-news/` with:

- Masthead (nameplate), headline, and byline layout.
- Two feature categories:
   - Perpetual Infrastructure Program (PIP)
   - Base True Information Format
- Story staging with `draft`, `scheduled`, and `published` statuses.
- Public email signup form for subscribers.
- One-click unsubscribe links in newsletter emails.

### Email setup (SMTP)

1. Copy `.env.example` values into your shell environment.
2. Set real SMTP credentials.
3. Restart your server process.

Example:

```bash
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_HOST_USER="your-email@example.com"
export EMAIL_HOST_PASSWORD="your-app-password"
export EMAIL_USE_TLS=True
export DEFAULT_FROM_EMAIL="BaseTrue Monthly <your-email@example.com>"
```

### Monthly send workflow

1. In Django admin, create an `Issue` for the target month/year.
2. Add `Story` entries to that issue and set `status=published` and `publish_at`.
3. Select the issue in admin and run action: `Email selected issues to active subscribers`.# gr_project
