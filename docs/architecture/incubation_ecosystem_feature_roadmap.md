# Incubation Ecosystem Feature Roadmap

## Purpose
This document is the technical North Star for the Idea-to-Business pipeline.
It defines the system scope, lifecycle phases, and implementation direction for recurring coding sessions.

## Lifecycle Model
The ecosystem is split into three backend phases:
1. Raw Idea Ingestion (Capture)
2. Seed Polish (Incubation)
3. Business Launch (Execution)

Each phase maps to a dedicated Service Object layer in Django.

## Current Architectural Baseline
- Dynamic taxonomy uses the Industry table (database-driven, not hard-coded).
- Idea lifecycle statuses: RAW -> SEED -> BUSINESS.
- Seed metadata supports flexible per-industry schema using PostgreSQL JSONB via Django JSONField.
- RAW -> SEED transition is handled through service + signal orchestration.

## Phase 1: Raw Idea Ingestion (Capture)
Goal: Ensure every submitted idea is categorized inside the 64-industry framework with reliable identity mapping.

### Core Features
1. Industry Taxonomy Service
- Reads industry options from the Industry table.
- Supports add/rename operations without application code changes.
- Exposes stable identifiers for API validation.

2. Idea Capture API
- Single ingestion endpoint for user idea submission.
- Validates user input against Industry.
- Creates an Idea record with initial status RAW.
- Returns normalized response payload for frontend and downstream services.

3. Unique Identity Mapping
- Similarity utility checks incoming ideas against existing user and global idea corpus.
- Flags probable duplicates/near-duplicates for review instead of hard blocking.
- Stores reference candidates for future read-only cross-reference querying.

### Suggested Service Objects
- IndustryTaxonomyService
- IdeaCaptureService
- IdeaIdentityMappingService

### Definition of Done
- API rejects invalid industry references.
- API always persists RAW status on successful ingestion.
- Similarity check produces deterministic and auditable candidate matches.

## Phase 2: Seed Polish (Incubation)
Goal: Transform unstructured RAW submissions into structured, actionable SEED assets.

### Core Features
1. Dynamic Metadata Engine (JSONB)
- Uses Seed.polish_notes as flexible metadata envelope.
- Enforces at least three industry-specific requirements per seed.
- Supports heterogeneous requirements across industries (for example: compliance, recipe, logistics, regulatory notes).

2. Idea Versioning and Snapshot History
- Captures snapshots of key lifecycle edits for traceability.
- Enables user-visible evolution from RAW text to polished SEED.
- Preserves immutable audit events for key transitions.

3. Collaborative Polishing Logic
- Allows multiple contributors to append and refine seed metadata.
- Preserves original author attribution and baseline submission integrity.
- Supports conflict-safe updates and simple merge strategy.

### Suggested Service Objects
- RawToSeedPolishService
- SeedMetadataValidationService
- IdeaSnapshotService
- CollaborativePolishService

### Definition of Done
- RAW -> SEED transition fails if required industry-specific metadata is incomplete.
- Every status-changing polish action is snapshot-audited.
- Multi-contributor updates do not overwrite original raw input.

## Phase 3: Business Launch (Execution)
Goal: Convert validated SEED records into production-ready BUSINESS entities.

### Core Features
1. Entity Transformation Service
- Triggered workflow converts validated Seed into Business record.
- Copies required normalized fields and launch metadata.
- Maintains deterministic parent-child linkage (Idea -> Seed -> Business).

2. Status Lifecycle Monitor
- Guardrail service blocks SEED -> BUSINESS unless mandatory industry fields are complete.
- Provides structured error responses indicating missing requirements.
- Supports asynchronous checks for large metadata payloads.

3. Read-Only Cross-Reference API
- Query endpoint surfaces associations across industries and business entities.
- Optimized for read-heavy discovery patterns.
- Supports filters by industry, status, relationship type, and similarity score.

### Suggested Service Objects
- SeedToBusinessTransformationService
- LifecycleReadinessService
- CrossReferenceQueryService

### Definition of Done
- No Business records are created from incomplete Seed metadata.
- Transformation produces traceable links to source Idea and Seed.
- Cross-reference API performs consistently under multi-industry query load.

## Cross-Cutting Platform Requirements
1. Observability
- Structured logs for all status transitions.
- Metrics for conversion funnel (RAW -> SEED -> BUSINESS).

2. Data Integrity and Governance
- Transaction-safe transitions.
- Immutable transition audit records.
- Clear ownership and contributor attribution.

3. Performance
- Indexed industry/status foreign keys.
- Indexed JSONB keys used by readiness checks and filters.
- Cached taxonomy lookups where appropriate.

4. Security
- Authenticated and authorized lifecycle operations.
- Role-aware write permissions for collaboration features.
- Read-only guarantees for cross-reference endpoints where required.

## Presentation View (Slide-Ready Summary)
1. Capture: Validate and classify ideas inside the dynamic 64-industry taxonomy.
2. Incubate: Enrich ideas with flexible, industry-specific metadata and collaborative polish.
3. Launch: Gate and transform validated seeds into business entities with full traceability.

## Prompt Templates for Future Coding Sessions
Use these prompts to keep implementation aligned with this roadmap.

### Phase 1 Prompt
I am working on Phase 1 (Raw Idea Ingestion). Using the Industry table as dynamic taxonomy, generate a Django service object and API endpoint that ingests a raw idea, validates industry, stores RAW status, and returns cross-reference candidate IDs.

### Phase 2 Prompt
I am working on Phase 2 (Seed Polish). Reference the Idea -> Seed ERD and implement a Django service object that upgrades RAW to SEED only if polish_notes contains at least 3 industry-specific requirements in JSONB.

### Phase 3 Prompt
I am working on Phase 3 (Business Launch). Implement a Django transformation service and lifecycle monitor that blocks SEED -> BUSINESS transitions until all mandatory metadata fields are complete, then creates a Business record with full lineage.

## Recommended Build Sequence
1. Harden Phase 1 API contracts and similarity utility.
2. Add snapshot/versioning and collaborative write controls in Phase 2.
3. Implement strict readiness gating and cross-reference query API in Phase 3.
4. Add integration tests for full lifecycle progression and failure gates.
