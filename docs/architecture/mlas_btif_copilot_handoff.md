# MLAS + BTIF Copilot Handoff

## Objective
Continue implementation of the captured MLAS/BTIF semantic system in GrassRoots with deterministic UI routing and preset-driven metadata expansion.

## Completed Ingestion Status
- MLAS capture session ended by explicit user signal: END MLAS.
- Strict capture mode was used for all provided chunks.
- UI rules and semantic preset definitions are now consolidated into canonical docs.

## Primary Artifacts
1. Canonical spec:
   - docs/architecture/mlas_btif_canonical_spec.md
2. Implementation-ready schema and contracts:
   - docs/architecture/mlas_btif_implementation_schemas.md
3. Validation checklist:
   - docs/operations/mlas_btif_validation_checklist.md

## Product Rules to Preserve
1. Routing function is canonical:
   - UI = f(phase, mlas, color, dewey, industry, metaphor, category)
2. Routing chain order is canonical:
   - phase -> mlas -> color -> dewey -> industry -> metaphor -> category -> layout_archetype -> component_pack
3. Semantic presets are first-class objects and must be deterministic and idempotent.
4. Phase families are non-optional:
   - Create/Immune/Operations
   - Post/Mycelium/Customer
   - Work/Botanist/Delivery-Executive

## Recommended Build Sequence
1. Data layer
   - Add Slide and SemanticPreset models.
   - Add routing output cache fields (phase_resolved, layout_archetype, component_pack, nav_group, page_signature, ui_category_resolved).
2. Routing engine
   - Implement pure resolver function from metadata.
   - Add service wrapper to compute and persist derived fields.
3. Preset engine
   - Implement apply-preset endpoint.
   - Guarantee idempotency.
4. API contracts
   - Expose resolved payload including ui/dewey/industry resolved sections.
5. UI integration
   - Consume resolved routing payload without hardcoded presentation logic.
6. QA
   - Run full checklist in docs/operations/mlas_btif_validation_checklist.md.

## Suggested Initial Ticket Breakdown
1. Create Django models + migration for Slide and SemanticPreset.
2. Seed canonical 12 presets using `SemanticPreset.name = phase.color.domain`.
3. Add resolver module + unit tests.
4. Add apply-preset API action + contract tests.
5. Add slide detail endpoint with resolved UI payload.
6. Add integration tests for one preset in each phase family.

Canonical preset names to seed:
- create.red.math
- create.blue.language
- create.yellow.arts
- create.green.science
- post.purple.statistics
- post.teal.literature
- post.orange.crafts
- post.lime.technology
- work.pink.history
- work.cyan.geography
- work.amber.industry
- work.greenlime.systems

## Explicit Resolver Rules
1. Work phase default is delivery; executive is explicit override.
2. mlas.term and mlas.meta may be optional at creation time, but if resolved `component_pack=deep-pack`, `mlas_meta` is required.

## Open Decisions
1. Industry mapping may need a normalization table for aliases.

## Immediate Next Step
Implement the data model and resolver first, then wire presets to remove manual UI configuration.
