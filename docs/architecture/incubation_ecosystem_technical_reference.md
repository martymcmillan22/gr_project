# Incubation Ecosystem: Technical Reference

## Purpose
Technical execution guide for the Idea-to-Business lifecycle roadmap.
Use this document as persistent coding context during backend/API development.

## System Scope
- Domain: Idea incubation across 64 industries
- Stack: Django, PostgreSQL, Service Objects, Signals
- Lifecycle states: RAW -> SEED -> BUSINESS
- Taxonomy: dynamic Industry table (database managed)

## Current Model Baseline
- Idea model with:
  - `industry` foreign key to `Industry`
  - `status` (`RAW`, `SEED`, `BUSINESS`)
  - user attribution and timestamps
- Seed model with:
  - one-to-one link to Idea
  - `polish_notes` JSONField (PostgreSQL JSONB)
  - germination and audit timestamps
- Business model with:
  - one-to-one link to Seed
  - launch-oriented fields

## Phase 1: RAW Ingestion (Capture)

### Responsibilities
1. Validate industry against dynamic taxonomy.
2. Persist RAW idea atomically.
3. Produce cross-reference candidates for similar prior ideas.

### Proposed Components
- `IndustryTaxonomyService`
- `IdeaCaptureService`
- `IdeaIdentityMappingService`

### API Contract (Draft)
POST `/api/ideas/`

Request body:
- `industry_id` (required)
- `raw_content` (required)
- optional contributor metadata

Response body:
- created `idea_id`
- `status=RAW`
- normalized `industry`
- `cross_reference_candidate_ids`

### Validation Rules
- Reject unknown industry IDs.
- Reject blank `raw_content`.
- Guarantee `status=RAW` on create.

## Phase 2: SEED Polish (Incubation)

### Responsibilities
1. Enforce structured metadata readiness using JSONB.
2. Promote RAW->SEED through service logic.
3. Track version/snapshot history.
4. Support collaborative enrichment without losing source truth.

### Proposed Components
- `RawToSeedPolishService`
- `SeedMetadataValidationService`
- `IdeaSnapshotService`
- `CollaborativePolishService`

### RAW->SEED Transition Rules
- Transition is invalid when:
  - `raw_content` is empty
  - `industry` is missing
  - `polish_notes.requirements` has fewer than 3 entries
- Transition should emit:
  - deterministic validation errors
  - audit event and snapshot on success

### JSONB Schema Shape (Example)
```json
{
  "industry": {
    "group_code": 1,
    "industry_code": 2,
    "name": "Digital Finance"
  },
  "requirements": ["compliance checklist", "risk model", "audit trail"],
  "notes": [],
  "promoted_at": "2026-06-27T12:00:00Z"
}
```

### Collaboration Rules
- Original `raw_content` remains immutable after first SEED promotion.
- Contributor deltas stored as additive updates.
- Conflicts resolved via explicit merge strategy (not silent overwrite).

## Phase 3: BUSINESS Launch (Execution)

### Responsibilities
1. Transform validated Seed into Business entity.
2. Block launch if readiness checks fail.
3. Expose read-only cross-industry relationship discovery.

### Proposed Components
- `SeedToBusinessTransformationService`
- `LifecycleReadinessService`
- `CrossReferenceQueryService`

### SEED->BUSINESS Gate Rules
- Mandatory industry-specific fields must be present.
- Lifecycle monitor returns explicit missing-field diagnostics.
- Business creation runs in single transaction with lineage links.

### API Contract (Draft)
POST `/api/businesses/from-seed/{seed_id}/`
- runs readiness checks
- creates business record on pass
- returns machine-readable error payload on fail

GET `/api/cross-reference/`
- read-only filters: industry, status, relationship_type, similarity_score
- optimized for query throughput and stable latency

## Cross-Cutting Non-Functional Requirements

### Observability
- Structured logs per transition event.
- Metrics: funnel conversion, gate failure causes, API latency.

### Integrity
- Transaction boundaries around status transitions.
- Immutable audit trail entries for lifecycle changes.

### Performance
- Indexes on `industry_id`, `status`, and high-use JSONB keys.
- Cache taxonomy lookups.
- Paginate and tune cross-reference queries.

### Security
- Authenticated writes, role-aware collaboration permissions.
- Read-only policy enforcement on cross-reference endpoints.

## Testing Strategy
1. Unit tests
- Service validation logic
- status transition guards
- JSONB requirement rules

2. Integration tests
- End-to-end RAW->SEED->BUSINESS path
- failure path assertions for missing required metadata

3. API tests
- contract-level request/response validation
- auth and permission boundaries

4. Performance checks
- p95 latency for cross-reference endpoint
- readiness gate throughput under load

## Build Sequence
1. Stabilize Phase 1 contracts and similarity scoring output.
2. Complete snapshot model and collaborative delta handling in Phase 2.
3. Implement strict readiness monitor and transformation flow in Phase 3.
4. Add cross-reference indexing and read-path optimization.

## Prompt Blocks for Coding Sessions

Phase 1 prompt:
Implement Phase 1 capture with dynamic industry validation and RAW persistence. Return cross-reference candidate IDs and deterministic error contracts.

Phase 2 prompt:
Implement RAW->SEED promotion service that enforces at least 3 industry-specific requirements in `polish_notes` JSONB and writes a snapshot entry.

Phase 3 prompt:
Implement SEED->BUSINESS transformation with lifecycle readiness checks and a read-only cross-reference API optimized for multi-industry queries.
