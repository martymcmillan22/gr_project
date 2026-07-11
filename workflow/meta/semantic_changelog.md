# Semantic Changelog

This file is updated by workflow release automation.

It records semantic rule updates, MLAS/BTIF changes, ontology updates, threshold updates, and safety gate updates.

## 0.6.1 - 2026-07-11T16:23:49.792275+00:00

### Semantic Rule Changes

- drift: propagation.mlas.semantic_tags must match normalized semantic_tags
- drift: propagation.mlas.mlas_tier must match feature mlas_tier
- drift: propagation.btif_route must match computed BTIF route
- drift: required artifact files must exist and include expected slug marker when applicable
- drift: propagation.synced_targets must point to existing files when populated
- inference: prefer explicit registry metadata over inferred defaults
- inference: fallback semantic_intent default is CaptureAndRoute
- inference: fallback mlas_tier default is Semantic Utility
- inference: fallback btif_classification default is GeneralFlow
- inference: fallback semantic_tags derive from slug tokens
- conflict: mlas_conflict when propagation.mlas differs from derived MLAS block
- conflict: btif_conflict when propagation.btif_route differs from derived route
- conflict: sync_conflict when propagated sync target path does not exist
- conflict: tag_conflict when semantic_tags are empty after normalization

### MLAS Tier Changes

- Semantic Utility

### BTIF Routing Changes

- IntakeFlow

### Ontology Updates

- intake
- pilot
- routing

### Threshold And Safety Gates

- confidence_thresholds: {'default_min_confidence': 0.85, 'fields': ['mlas_tier', 'btif_classification', 'semantic_intent', 'semantic_tags']}
- autofix_safety_gates: {'safe_conflict_types': ['btif_conflict', 'mlas_conflict', 'tag_conflict'], 'requires_force_unsafe_for_other_types': True}

