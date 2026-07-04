# PostgreSQL Indexing Strategy for Cross-Reference Engine

## Goal
Keep read-only hierarchical cross-reference queries across 64 industries under 100ms at multi-million row scale.

## Scope
This strategy is based on the ERD concepts:
- `INDUSTRY`
- `IDEA`
- `SEED`
- `BUSINESS`
- `CROSS_REFERENCE`

and on high-frequency read patterns such as:
- industry filtered traversal
- relationship lookups by source/target
- status-constrained discovery
- metadata filtering in JSONB

## Core Query Patterns to Optimize
1. Find related entities from a source node:
```sql
SELECT cr.target_id, cr.relationship_type, cr.score
FROM cross_reference cr
WHERE cr.source_id = $1
ORDER BY cr.score DESC
LIMIT 100;
```

2. Find cross-industry relationships with filters:
```sql
SELECT cr.*
FROM cross_reference cr
JOIN business b1 ON b1.id = cr.source_business_id
JOIN business b2 ON b2.id = cr.target_business_id
WHERE b1.industry_id = $1
  AND b2.industry_id = $2
  AND cr.relationship_type = $3
ORDER BY cr.score DESC
LIMIT 100;
```

3. Filter by lifecycle status + industry:
```sql
SELECT i.id, i.status, i.updated_at
FROM idea i
WHERE i.industry_id = $1
  AND i.status = 'SEED'
ORDER BY i.updated_at DESC
LIMIT 200;
```

4. Filter by JSONB mandatory metadata presence:
```sql
SELECT s.id
FROM seed s
WHERE s.polish_notes @> '{"requirements": []}'::jsonb;
```

## Recommended Index Set

### 1) Industry + Status + Time (Idea)
```sql
CREATE INDEX CONCURRENTLY idx_idea_industry_status_updated
ON seeds_idea (industry_id, status, updated_at DESC);
```
Why:
- Supports most lifecycle list queries.
- Enables index-backed sorting for recent-first pagination.

### 2) Status Partial Indexes (Idea)
```sql
CREATE INDEX CONCURRENTLY idx_idea_seed_only_updated
ON seeds_idea (updated_at DESC)
WHERE status = 'SEED';

CREATE INDEX CONCURRENTLY idx_idea_business_only_updated
ON seeds_idea (updated_at DESC)
WHERE status = 'BUSINESS';
```
Why:
- Smaller indexes than full-table composites.
- Faster targeted reads for phase-specific dashboards.

### 3) JSONB GIN Index (Seed Metadata)
```sql
CREATE INDEX CONCURRENTLY idx_seed_polish_notes_gin
ON seeds_seed
USING GIN (polish_notes jsonb_path_ops);
```
Why:
- Accelerates containment/path queries over `polish_notes`.
- Critical for readiness checks and metadata filters.

### 4) Seed to Idea Join Support
```sql
CREATE INDEX CONCURRENTLY idx_seed_idea_id
ON seeds_seed (idea_id);
```
Why:
- Ensures cheap join paths between lifecycle stages.

### 5) Business to Seed Join Support
```sql
CREATE INDEX CONCURRENTLY idx_business_seed_id
ON seeds_business (seed_id);
```
Why:
- Speeds lineage and launch-readiness reporting queries.

### 6) Cross-Reference Directed Graph Access
Assuming table shape includes: `source_id`, `target_id`, `relationship_type`, `score`, `created_at`.
```sql
CREATE INDEX CONCURRENTLY idx_cr_source_score
ON cross_reference (source_id, score DESC);

CREATE INDEX CONCURRENTLY idx_cr_target_score
ON cross_reference (target_id, score DESC);

CREATE INDEX CONCURRENTLY idx_cr_reltype_source_score
ON cross_reference (relationship_type, source_id, score DESC);
```
Why:
- Covers "from node" and "to node" traversal.
- Supports high-cardinality filtering by relationship type.

### 7) Duplicate-Edge Prevention and Fast Existence Checks
```sql
CREATE UNIQUE INDEX CONCURRENTLY ux_cr_source_target_type
ON cross_reference (source_id, target_id, relationship_type);
```
Why:
- Prevents redundant edges.
- Enables O(log n) existence checks.

## Optional Scale Enhancements

### A) Partition Large Cross-Reference Table
If row count grows into tens/hundreds of millions:
- Partition by hash on `source_id` for even distribution.
- Keep local indexes per partition.

### B) Covering Indexes (INCLUDE)
When heap lookups dominate:
```sql
CREATE INDEX CONCURRENTLY idx_cr_source_score_cover
ON cross_reference (source_id, score DESC)
INCLUDE (target_id, relationship_type, created_at);
```

### C) Materialized View for Hot Relationship Reads
Precompute top-N relationships per industry pair.
Refresh incrementally or on schedule.

## Query and Planner Guardrails
- Keep predicates sargable (avoid function-wrapped indexed columns).
- Use keyset pagination instead of deep OFFSET.
- Keep statistics current:
```sql
ANALYZE seeds_idea;
ANALYZE seeds_seed;
ANALYZE seeds_business;
ANALYZE cross_reference;
```
- Confirm plan quality with:
```sql
EXPLAIN (ANALYZE, BUFFERS)
<query>;
```

## Performance Budget Targets
- Point relationship lookup by source: p95 <= 25ms
- Industry-filtered graph traversal: p95 <= 60ms
- JSONB readiness filters: p95 <= 40ms
- Composite endpoint budget (API + serialization): <= 100ms

## Implementation Order
1. Add core lifecycle indexes on `seeds_idea` and `seeds_seed`.
2. Add `cross_reference` directed and uniqueness indexes.
3. Benchmark top 5 read queries with `EXPLAIN ANALYZE`.
4. Add covering indexes only where heap fetches remain high.
5. Add partitioning/materialized views only after measured need.

## Migration Guidance (Django)
For production-safe online indexing:
- Use `RunSQL` migrations with `CREATE INDEX CONCURRENTLY`.
- Mark migration `atomic = False` because concurrent index creation cannot run inside a transaction.

## Prompt for Next Build Step
Based on this indexing plan, generate a Django migration with `RunSQL` statements using `CREATE INDEX CONCURRENTLY` for `seeds_idea`, `seeds_seed`, and a new `cross_reference` table, with safe reverse SQL and `atomic = False`.
