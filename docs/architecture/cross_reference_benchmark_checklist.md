# Cross-Reference Benchmark Checklist

## Objective
Validate that read-only cross-reference queries remain under 100ms at realistic scale.

## Prerequisites
- PostgreSQL running with latest migrations applied.
- Index migration applied: `seeds.0003_cross_reference_and_lifecycle_indexes`.
- Representative data volume loaded (minimum target: 1M+ cross-reference rows).

## Benchmark Dataset Targets
1. Industries
- 64 industries present.

2. Lifecycle entities
- 2M+ ideas
- 500k+ seeds
- 100k+ businesses

3. Graph edges
- 1M+ cross-reference rows
- Diverse `relationship_type` values
- Non-uniform score distribution

## Core Query Benchmarks

### Q1: Source Node Top-N
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT target_business_id, relationship_type, score
FROM seeds_crossreference
WHERE source_business_id = $1
ORDER BY score DESC
LIMIT 100;
```
Target: p95 <= 25ms

### Q2: Target Node Reverse Lookup
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT source_business_id, relationship_type, score
FROM seeds_crossreference
WHERE target_business_id = $1
ORDER BY score DESC
LIMIT 100;
```
Target: p95 <= 25ms

### Q3: Relationship Type + Source
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT target_business_id, score
FROM seeds_crossreference
WHERE relationship_type = 'similar'
  AND source_business_id = $1
ORDER BY score DESC
LIMIT 100;
```
Target: p95 <= 30ms

### Q4: Industry + Status Feed
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, updated_at
FROM seeds_idea
WHERE industry_id = $1
  AND status = 'SEED'
ORDER BY updated_at DESC
LIMIT 200;
```
Target: p95 <= 40ms

### Q5: JSONB Requirement Presence
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM seeds_seed
WHERE polish_notes @> '{"requirements": []}'::jsonb
LIMIT 500;
```
Target: p95 <= 40ms

## API Budget Targets
- Cross-reference endpoint end-to-end (DB + app + serialization): p95 <= 100ms
- Time to first byte: p95 <= 120ms

## Verification Steps
1. Run `ANALYZE` after data load:
```sql
ANALYZE seeds_idea;
ANALYZE seeds_seed;
ANALYZE seeds_business;
ANALYZE seeds_crossreference;
```
2. Execute each benchmark query 30-50 times with varied parameters.
3. Record p50/p95/p99 latency and buffer reads.
4. Confirm index usage in query plans.
5. Capture regressions against previous baseline.

## Failure Triage
- If sequential scans appear, verify predicate shape and stats freshness.
- If heap fetches are high, consider covering indexes with `INCLUDE`.
- If write overhead is acceptable but reads still slow, evaluate partitioning on `source_business_id`.
- If app latency dominates DB latency, profile serializer and network path.

## Exit Criteria
- All core query targets pass at p95.
- API p95 remains under 100ms for top read endpoints.
- Baseline report saved for future regression comparisons.
