# Workflow Architecture Overview

## Purpose

This document defines the canonical architecture of the workflow platform under workflow/.

The workflow platform is the deterministic command center for:

- feature scaffolding
- semantic classification
- synchronization to runtime stubs
- semantic propagation and consistency checks

## Canonical Categories

1. database_design/mermaid_erds
2. logic_design/mermaid_sequences
3. ui_templates/penpot_templates
4. ui_components/penpot_components

## Core Engine Modules

Engine package: workflow/_engine/

- scaffold.py: deterministic feature scaffold generation
- registry.py: registry load/save and feature insertion
- validate.py: registry shape validation
- mlas_integration.py: MLAS semantic classification mapping
- btif_router.py: BTIF route assignment and consistency helpers
- sync_erd.py: ERD to backend model stub sync
- sync_sequence.py: sequence to backend logic stub sync
- sync_ui_template.py: UI template to React page stub sync
- sync_ui_component.py: UI component spec to generated design-system component sync
- semantic_propagation.py: semantic metadata propagation back into registry
- semantic_drift.py: artifact and metadata drift detection
- semantic_infer.py: deterministic metadata inference and recommendations
- semantic_conflicts.py: semantic conflict detection and autofix support
- visualize.py: workflow visualization generation

## CLI Surface

Entrypoint: workflow/cli.py

Supported commands:

- new-feature
- validate
- validate-suite
- classify
- semantic-check
- sync --feature <slug>
- sync-all
- visualize --feature <slug>
- visualize-all
- semantic-drift
- semantic-infer
- semantic-resolve

## Registry

Registry file: workflow/registry.json

Top-level fields:

- schema_version
- workflow_version
- features

Feature fields:

- name
- slug
- mlas_tier
- btif_classification
- semantic_intent
- semantic_tags
- paths
- status
- propagation

## Sync Outputs

Generated output targets:

- platform_core/workflow_generated/models/
- platform_core/workflow_generated/logic/
- ui_apps/workflow_generated/pages/
- workflow/ui_components/penpot_components/generated/

## Architectural Rule

workflow/ is the canonical workflow source.
Retired legacy locations must not be reintroduced as workflow origins.
