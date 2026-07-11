# Semantic Inference Overview

## Purpose

This document defines deterministic semantic inference behavior for workflow features.

## Inference Module

- workflow/_engine/semantic_infer.py

## Inferred Fields

- mlas_tier
- btif_classification
- semantic_intent
- semantic_tags
- feature_lineage
- dependency_classification

## Command

- python3 workflow/cli.py semantic-infer

## Output Model

The inference report returns per feature:

- predicted
- confidence
- justification
- recommended_updates

## Deterministic Rule

Inference uses explicit registry fields first and only falls back to deterministic defaults when fields are missing.
No probabilistic model or external context is used.
