# Incubation Ecosystem One-Page Handout

## What This Ecosystem Does
The Incubation Ecosystem converts unstructured ideas into validated business entities through a governed, traceable lifecycle:
1. RAW capture
2. SEED incubation
3. BUSINESS launch

## Why It Matters
- Scales across 64 industries without hard-coded logic.
- Preserves quality with readiness gates and audit trails.
- Enables discovery across industries through read-only cross-referencing.

## Lifecycle at a Glance

### Phase 1: Capture (RAW)
- Dynamic industry taxonomy from database tables.
- Unified ingestion API validates industry and stores RAW status.
- Similarity mapping flags candidate related ideas.

### Phase 2: Incubate (SEED)
- JSONB metadata stores industry-specific requirements.
- Snapshot/version history tracks idea evolution.
- Collaborative polishing supports multiple contributors safely.

### Phase 3: Launch (BUSINESS)
- Service transforms validated seeds into business entities.
- Lifecycle monitor blocks launch when mandatory fields are missing.
- Read-only cross-reference API supports relationship discovery.

## Technical Principles
- Dynamic data model over hard-coded enum logic.
- Service-object orchestration for lifecycle transitions.
- Transactional state changes with deterministic validation.
- Auditability and attribution built into workflow.

## Success Metrics
- RAW->SEED conversion rate
- SEED->BUSINESS conversion rate
- Readiness gate pass/fail trend
- Cross-reference API p95 latency

## What Is Already Implemented
- Dynamic industry relationship on `Idea` via foreign key.
- Status model and lifecycle path: RAW -> SEED -> BUSINESS.
- JSONB-backed seed metadata (`polish_notes`).
- RAW->SEED promotion via service + signal orchestration.

## Immediate Next Build Priorities
1. Harden capture API contracts and cross-reference candidate scoring.
2. Add snapshot history and collaboration controls in SEED phase.
3. Add launch-readiness monitor and strict SEED->BUSINESS gates.
4. Optimize read-only cross-reference querying for sub-100ms responses.

## Decision
Adopt this roadmap as the shared baseline for product planning, architecture decisions, and coding prompts.
