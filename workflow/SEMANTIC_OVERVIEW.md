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

## Semantic Intelligence Modules

- workflow/_engine/semantic_drift.py
- workflow/_engine/semantic_infer.py
- workflow/_engine/semantic_conflicts.py

These modules add drift detection, metadata inference, and deterministic conflict resolution.

## Hardening Policies

- Inference confidence can be enforced with a minimum threshold.
- Resolve autofix is blocked when unsafe conflict types are present unless explicitly overridden.

## Deterministic Rule

All semantic decisions must derive from explicit registry fields and workflow artifacts.
No semantic inference may bypass declared mlas_tier, semantic_intent, or btif_classification.
