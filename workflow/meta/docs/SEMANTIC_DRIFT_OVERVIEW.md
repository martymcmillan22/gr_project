# Semantic Drift Overview

## Purpose

This document defines how semantic drift is detected across workflow artifacts, registry metadata, and propagation outputs.

## Drift Module

- workflow/_engine/semantic_drift.py

## Drift Types

- ERD structure drift
- Sequence flow drift
- UI template intent drift
- Component naming drift
- MLAS tier drift
- BTIF routing drift
- Tag mismatch drift
- Sync target drift

## Command

- python3 workflow/cli.py semantic-drift

## Output Model

The drift report is deterministic JSON by feature slug with:

- drift_count
- drift[]
  - type
  - reason
  - severity

## Recommended Flow

1. Run semantic-drift
2. Run semantic-infer for metadata recommendations
3. Run semantic-resolve for conflicts
4. Run sync-all and visualize-all
5. Run validate-suite
