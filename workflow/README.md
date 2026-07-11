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
