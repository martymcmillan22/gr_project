# Workflow Semantic Overview

## Purpose

This document defines how workflow artifacts are interpreted semantically through MLAS and BTIF.

## Semantic Inputs Per Feature

From workflow/registry.json each feature provides:

- mlas_tier
- btif_classification
- semantic_intent
- semantic_tags
- paths

These fields are required for deterministic semantic operations.

## MLAS Layer

Module: workflow/_engine/mlas_integration.py

Responsibilities:

- normalize semantic tags
- classify feature semantic metadata
- validate MLAS-facing semantic fields
- build MLAS classification report

Output example:

- slug
- mlas_tier
- semantic_intent
- semantic_tags (normalized)

## BTIF Layer

Module: workflow/_engine/btif_router.py

Responsibilities:

- assign deterministic BTIF routes
- validate BTIF routing prerequisites
- generate routing table from registry features

Route format:

btif://<btif_classification>/<semantic_intent>/<slug>

## Semantic Validation

Validation runner: workflow/validation/suite.py

Semantic checks enforce:

- non-empty semantic_intent
- non-empty normalized semantic_tags
- non-empty mlas_tier
- non-empty btif_classification
- valid status values
- artifact paths exist for each feature

## Semantic Propagation

Module: workflow/_engine/semantic_propagation.py

Propagation writes into feature.propagation:

- propagation.mlas
- propagation.btif_route
- propagation.synced_targets

This keeps semantic and sync outputs aligned with registry state.

## CLI Semantic Commands

- python3 workflow/cli.py classify
- python3 workflow/cli.py semantic-check
- python3 workflow/cli.py sync --feature <slug>
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py semantic-drift
- python3 workflow/cli.py semantic-infer
- python3 workflow/cli.py semantic-resolve
- python3 workflow/cli.py semantic-infer --enforce-threshold --min-confidence 0.85
- python3 workflow/cli.py semantic-resolve --apply [--force-unsafe]
- python3 workflow/cli.py ai-context
- python3 workflow/cli.py ai-export
- python3 workflow/cli.py release --approve-semantic-changes
- python3 workflow/cli.py release-notes
- python3 workflow/cli.py evolve-feature --feature <slug>
- python3 workflow/cli.py evolve-all
- python3 workflow/cli.py evolve-preview
- python3 workflow/cli.py expand
- python3 workflow/cli.py expand-all
- python3 workflow/cli.py expand-preview

## Semantic Intelligence Modules

- workflow/_engine/semantic_drift.py
- workflow/_engine/semantic_infer.py
- workflow/_engine/semantic_conflicts.py

These modules add drift detection, metadata inference, and deterministic conflict resolution.

## Hardening Policies

- Inference confidence can be enforced with a minimum threshold.
- Resolve autofix is blocked when unsafe conflict types are present unless explicitly overridden.

## Release Governance Policies

- MLAS tier changes require explicit semantic approval at release time.
- BTIF route changes require explicit semantic approval at release time.
- semantic intent changes require explicit semantic approval at release time.
- tag ontology changes require explicit semantic approval at release time.
- release gates enforce drift, inference, conflict, validation, sync, visualization, and AI export checks.

## Semantic Evolution Policies

- evolution proposals are non-destructive by default.
- proposal apply-mode requires explicit governance approvals.
- MLAS/BTIF and ontology evolution require semantic approval.
- ERD/sequence evolution requires structural approval.
- UI/component evolution requires sync approval.

## Semantic Expansion Policies

- expansion proposals are non-destructive by default.
- new feature proposals require explicit expansion approval.
- new semantic intents, MLAS/BTIF patterns, and ontology additions require semantic approval.
- cross-feature integrations require structural approval.
- multi-feature bundles require sync approval.

## AI Semantic Export

AI semantic context file:

- workflow/semantic_context.json

This export provides:

- MLAS tier definitions
- BTIF routing definitions
- semantic intent definitions
- tag ontology
- semantic lineage
- drift, inference, and conflict rules
- confidence thresholds
- autofix safety gates

## Deterministic Rule

All semantic decisions must derive from explicit registry fields and workflow artifacts.
No semantic inference may bypass declared mlas_tier, semantic_intent, or btif_classification.
