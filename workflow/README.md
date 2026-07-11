# Workflow Command Center

This directory is the unified command center and canonical source for workflow artifacts used to design and build apps, features, UI flows, backend logic, and schema flows.

## Categories

1. database_design/mermaid_erds
2. logic_design/mermaid_sequences
3. ui_templates/penpot_templates
4. ui_components/penpot_components

## Source Mapping (Hard-Moved)

### database_design/mermaid_erds
- docs/architecture/data_schema.mmd
- docs/architecture/mermaid/ERD.txt
- flow_diagram/seed_creator.drawio

### logic_design/mermaid_sequences
- docs/architecture/logic_flow.mmd
- docs/architecture/mermaid/sequence_diagram.txt
- docs/MMD_workflow_guide.txt

### ui_templates/penpot_templates
- ui_template_library/react_onepager/src/layout/AppShell.tsx
- ui_template_library/react_onepager/src/sections/*
- ui_template_library/react_onepager/src/theme.css
- ui_template_library/react_onepager/src/index.ts

### ui_components/penpot_components
- components/ui/*
- components/grassroots/*
- design-system/tokens-penpot-export.json
- design-system/PENPOT_SOURCE.md

## Reorganization Mode

Phase 2 hard move is active. The mapped source artifacts were relocated into workflow/ and old canonical locations were retired.

## Phase-3 Engine MVP

The workflow automation engine lives in workflow/_engine and is exposed by workflow/cli.py.

### Commands

- python workflow/cli.py new-feature --name "Feature Name" --mlas-tier "TierName" --btif-classification "ClassName" --semantic-intent "IntentName" --semantic-tags tag1 tag2
- python workflow/cli.py validate
- python workflow/cli.py validate-suite
- python workflow/cli.py classify
- python workflow/cli.py semantic-check
- python workflow/cli.py sync --feature <slug>
- python workflow/cli.py sync-all
- python workflow/cli.py visualize --feature <slug>
- python workflow/cli.py visualize-all
- python workflow/cli.py semantic-drift
- python workflow/cli.py semantic-infer
- python workflow/cli.py semantic-resolve [--apply]
- python workflow/cli.py semantic-infer --enforce-threshold --min-confidence 0.85
- python workflow/cli.py semantic-resolve --apply [--force-unsafe]
- python workflow/cli.py ai-context
- python workflow/cli.py ai-export
- python workflow/cli.py ai-new-feature --name "Feature Name" [--sync]
- python workflow/cli.py version
- python workflow/cli.py bump-version --part patch
- python workflow/cli.py release --bump patch
- python workflow/cli.py release-notes
- python3 -m unittest discover workflow/tests -v

### Generated Outputs for new-feature

- workflow/database_design/mermaid_erds/<slug>.erd.mmd
- workflow/logic_design/mermaid_sequences/<slug>.sequence.mmd
- workflow/ui_templates/penpot_templates/features/<slug>/template.md
- workflow/ui_components/penpot_components/features/<slug>/component.md

### Metadata Source of Truth

Feature metadata is stored in workflow/registry.json and validated with workflow/cli.py validate.

## Phase-3 Slice 3: Semantic Integration

Semantic integration modules:

- workflow/_engine/mlas_integration.py
- workflow/_engine/btif_router.py

Semantic checks enforce deterministic consistency for:

- semantic_intent
- semantic_tags
- mlas_tier
- btif_classification

## Phase-3 Slice 4: Sync Layer + Semantic Propagation

Sync modules:

- workflow/_engine/sync_erd.py
- workflow/_engine/sync_sequence.py
- workflow/_engine/sync_ui_template.py
- workflow/_engine/sync_ui_component.py
- workflow/_engine/semantic_propagation.py

Sync behavior:

- ERD to backend model stubs under platform_core/workflow_generated/models/
- sequence to backend logic stubs under platform_core/workflow_generated/logic/
- UI templates to React pages under ui_apps/workflow_generated/pages/
- UI component specs to generated design-system components under workflow/ui_components/penpot_components/generated/

Semantic propagation behavior:

- normalizes semantic_tags
- updates propagation.mlas report for each feature
- updates propagation.btif_route
- records propagation.synced_targets

## Phase-4 Slice 2: Workflow Visualization Layer

Visualization module:

- workflow/_engine/visualize.py

CLI commands:

- python workflow/cli.py visualize --feature <slug>
- python workflow/cli.py visualize-all

Generated visual outputs:

- workflow/visualizations/features/<slug>.visualization.md
- workflow/visualizations/feature-dependency-graph.mmd
- workflow/visualizations/mlas-tier-map.mmd
- workflow/visualizations/btif-routing-map.mmd

## Phase-4 Slice 3: Semantic Engine Deep Integration

Semantic intelligence modules:

- workflow/_engine/semantic_drift.py
- workflow/_engine/semantic_infer.py
- workflow/_engine/semantic_conflicts.py

New semantic commands:

- python workflow/cli.py semantic-drift
- python workflow/cli.py semantic-infer
- python workflow/cli.py semantic-resolve [--apply]

Additional docs:

- workflow/SEMANTIC_DRIFT_OVERVIEW.md
- workflow/SEMANTIC_INFERENCE_OVERVIEW.md

## Phase-4 Slice 4: Semantic Hardening

Hardening policies:

- inference confidence threshold gate via `--enforce-threshold`
- configurable threshold via `--min-confidence`
- autofix safety gate that blocks `--apply` when unsafe conflict types are present
- explicit override via `--force-unsafe`

Test suite:

- workflow/tests/test_semantic_infer.py
- workflow/tests/test_semantic_conflicts.py

## Phase-4 Slice 5: AI-Native Integration

AI onboarding and command files:

- workflow/ai_hints.json
- workflow/ai_navigation.json
- workflow/semantic_context.json

AI prompt surface:

- workflow/ai_prompts/new_feature_prompt.txt
- workflow/ai_prompts/semantic_inference_prompt.txt
- workflow/ai_prompts/drift_analysis_prompt.txt
- workflow/ai_prompts/conflict_resolution_prompt.txt
- workflow/ai_prompts/visualization_prompt.txt

AI template surface:

- workflow/ai_templates/feature.json

AI-native CLI commands:

- python workflow/cli.py ai-context
- python workflow/cli.py ai-export
- python workflow/cli.py ai-new-feature --name "Feature Name" [--sync]

AI integration docs:

- workflow/COPILOT_INTEGRATION_GUIDE.md
- workflow/COPILOT_OPERATING_MODEL.md

## Phase-4 Slice 6: Release And Governance System

Versioning and governance files:

- workflow/version.json
- workflow/governance_policy.json
- workflow/semantic_changelog.md

Release pipeline scripts:

- workflow/release.py
- workflow/release_notes.py

Release docs:

- workflow/RELEASE_OVERVIEW.md
- workflow/VERSIONING_GUIDE.md

Release and version CLI commands:

- python3 workflow/cli.py version
- python3 workflow/cli.py bump-version --part major|minor|patch
- python3 workflow/cli.py release --bump patch [--approve-semantic-changes]
- python3 workflow/cli.py release-notes

Release safety checks:

- semantic-drift must pass
- semantic-infer confidence policy must pass
- semantic-resolve must pass
- validate-suite must pass
- visualize-all must pass
- sync-all must pass
- ai-export must pass
