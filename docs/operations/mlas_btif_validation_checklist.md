# MLAS + BTIF Validation Checklist

## Purpose
Use this checklist to verify that metadata, UI routing, and presets behave correctly in end-to-end slide rendering.

## Test Scope
- Metadata integrity
- Routing determinism
- Preset expansion
- UI behavior by metaphor
- Navigation and signature mapping
- Failure-mode handling

## Pre-Run Setup
1. Ensure test data contains at least one slide for each phase.
2. Ensure all 12 colors appear in seeded slides.
3. Ensure preset registry includes all canonical presets.
4. Ensure API response exposes resolved fields: nav_group, page_signature, layout_archetype, component_pack, ui_category.

## A) Metadata Integrity
1. Required fields present:
   - phase
   - color.primary
   - mlas.subject
   - mlas.branch
   - dewey.code
2. Optional fields accepted without breaking:
   - mlas.term
   - mlas.meta
   - industry.group
   - industry.sub_industry
3. Invalid phase is rejected.
4. Unknown color is rejected.
5. Invalid Dewey value is rejected.

Pass criteria: invalid requests return validation errors with field-level detail.

## B) Phase -> Category Mapping
1. Create resolves to operations by default.
2. Post resolves to customer by default.
3. Work resolves to delivery by default.
4. Work + executive override resolves to executive.

Pass criteria: resolved ui.category matches rule table.

## C) Color -> Layout Mapping
1. red/blue/yellow/green -> matrix
2. purple/teal/orange/lime -> journey
3. pink/cyan/amber/green-lime -> pipeline

Pass criteria: each color maps to exactly one layout, no ambiguity.

## D) MLAS Depth -> Component Pack
1. subject only -> foundational-pack
2. branch present -> narrative-pack
3. term present -> structural-pack
4. meta present -> deep-pack

Pass criteria: deepest available MLAS depth always wins.

## E) Dewey -> Navigation
1. 100-400 -> foundations
2. 500-800 -> information
3. 900-1000 -> systems

Pass criteria: each tested Dewey code appears in expected nav group.

## F) Industry -> Signature
1. Financials -> analytical
2. Communications -> narrative
3. Consumer -> experiential
4. Industrials -> operational

Pass criteria: page_signature aligns with industry mapping.

## G) Metaphor Behavioral Rules
### Immune system behavior checks
1. Missing metadata is flagged.
2. Anomalous combinations are highlighted.
3. Structural relationship view is available.

### Mycelium behavior checks
1. Branch view is enabled.
2. Pattern replication view is enabled.
3. Lineage view is enabled.

### Botanist behavior checks
1. Evolution timeline is enabled.
2. Dependency graph is enabled.
3. Constraint panel is enabled.

Pass criteria: UI behavior profile changes with metaphor family.

## H) Preset Expansion
1. Apply PURPLE.post.statistics.
2. Confirm inherited fields:
   - phase: post
   - color: purple
   - mlas.branch: sacp
   - dewey.code: 500
   - metaphor: mycelium
   - ui.category: customer
   - layout: journey
   - components: narrative-pack
3. Re-apply same preset.

Pass criteria:
- First apply fills expected metadata.
- Second apply is idempotent.

## I) Canonical Preset Family Coverage
1. Create presets (4) each resolve to operations + matrix archetype.
2. Post presets (4) each resolve to customer + journey archetype.
3. Work presets (4) each resolve to delivery/executive + pipeline archetype.

Pass criteria: all 12 presets validate without override errors.

## J) Negative and Boundary Tests
1. Dewey = 400 and 500 boundaries map correctly.
2. Dewey = 800 and 900 boundaries map correctly.
3. Unknown preset key returns not found.
4. Preset with missing registry fields fails fast.
5. Mixed-phase mismatch (e.g., phase=create + metaphor=mycelium) is either rejected or explicitly logged as override.

Pass criteria: boundary behavior is deterministic and documented.

## K) Regression Pack (Minimum)
Run these before release:
1. One fixture per phase and one fixture per layout archetype.
2. One fixture per navigation group.
3. One fixture per page signature.
4. One fixture for each of the 12 canonical presets.

## Validation Output Template
Use this structure per test run:

```text
Run date:
Commit:
Environment:

Checks passed:
Checks failed:
Open issues:
Blocking issues:

Sign-off:
```
