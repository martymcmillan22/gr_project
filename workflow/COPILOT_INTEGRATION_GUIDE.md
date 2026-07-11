# Copilot Integration Guide

This guide defines how Copilot and VS Code AI assistants should operate inside the workflow platform.

## Scope

This guide applies to workflow planning, semantic reasoning, feature generation, sync, visualization, and mutation operations under workflow/.

## AI Behavior Rules

1. Treat workflow as a semantic operating system.
2. Bootstrap every workflow task by reading:
- workflow/ai_hints.json
- workflow/ai_navigation.json
- workflow/semantic_context.json
3. Prefer command-first mutation for deterministic behavior.
4. Use workflow templates and prompts before proposing feature metadata.
5. Preserve naming continuity across feature name, slug, semantic intent, MLAS tier, and BTIF class.
6. Avoid direct registry mutation when CLI command equivalents exist.

## Semantic Reasoning Rules

1. Use explicit registry metadata as source of truth.
2. Use deterministic fallback inference only when fields are missing.
3. Validate semantic intent, semantic tags, MLAS tier, and BTIF classification against semantic_context.json.
4. For semantic reasoning workflows, use these prompts:
- workflow/ai_prompts/semantic_inference_prompt.txt
- workflow/ai_prompts/drift_analysis_prompt.txt
- workflow/ai_prompts/conflict_resolution_prompt.txt
5. Never infer unsafe semantic changes without explicit user approval.

## CLI Usage Patterns

Primary command surface:

- python3 workflow/cli.py ai-context
- python3 workflow/cli.py ai-export
- python3 workflow/cli.py ai-new-feature --name "Feature Name" --dry-run
- python3 workflow/cli.py ai-new-feature --name "Feature Name" --sync
- python3 workflow/cli.py semantic-infer --enforce-threshold --min-confidence 0.85
- python3 workflow/cli.py semantic-drift
- python3 workflow/cli.py semantic-resolve
- python3 workflow/cli.py semantic-resolve --apply
- python3 workflow/cli.py sync --feature <slug>
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py visualize --feature <slug>
- python3 workflow/cli.py visualize-all
- python3 workflow/cli.py version
- python3 workflow/cli.py bump-version --part patch
- python3 workflow/cli.py release --bump patch [--approve-semantic-changes]
- python3 workflow/cli.py release-notes
- python3 workflow/cli.py evolve-feature --feature <slug>
- python3 workflow/cli.py evolve-all
- python3 workflow/cli.py evolve-preview
- python3 workflow/cli.py expand
- python3 workflow/cli.py expand-all
- python3 workflow/cli.py expand-preview
- python3 workflow/cli.py refactor-feature --feature <slug>
- python3 workflow/cli.py refactor-all
- python3 workflow/cli.py refactor-preview
- python3 workflow/cli.py improve-feature --feature <slug>
- python3 workflow/cli.py improve-all
- python3 workflow/cli.py improve-preview

Mutation policy:

1. Use ai-new-feature or new-feature for feature creation.
2. Use sync and sync-all for generated outputs.
3. Use visualize and visualize-all for diagrams.
4. Use semantic-resolve --apply only when safe.

## Safety Gates

1. Respect autofix safety plan from semantic-resolve output.
2. Safe conflict classes are only:
- mlas_conflict
- btif_conflict
- tag_conflict
3. Treat sync_conflict as unsafe.
4. Never run semantic-resolve --force-unsafe unless user explicitly asks for unsafe override.
5. If unsafe conflicts exist, stop, report, and ask for explicit instruction.
6. If semantic governance deltas are detected, require explicit approval before release.
7. If evolution proposals include governance requirements, require matching explicit approvals before apply mode.
8. If expansion proposals include governance requirements, require matching explicit approvals before apply mode.
9. If refactor proposals include governance requirements, require matching explicit approvals before apply mode.
10. If running unified improvement cycle, require engine approvals plus semantic, structural, and sync approvals.

## Confidence Thresholds

1. Default minimum confidence threshold is 0.85.
2. Enforce threshold with:
- python3 workflow/cli.py semantic-infer --enforce-threshold --min-confidence 0.85
3. If policy fails, do not auto-apply semantic changes.
4. Report failing fields and recommended updates before proceeding.

## Examples

### Example 1: Refresh AI context

1. python3 workflow/cli.py ai-export
2. python3 workflow/cli.py ai-context

Expected outcome:
- workflow/ai_hints.json updated
- workflow/ai_navigation.json updated
- workflow/semantic_context.json updated

### Example 2: AI-assisted feature creation (safe path)

1. python3 workflow/cli.py ai-new-feature --name "Patient Intake" --dry-run
2. Review generated semantic fields and paths.
3. python3 workflow/cli.py ai-new-feature --name "Patient Intake" --sync
4. python3 workflow/cli.py validate-suite
5. python3 workflow/cli.py visualize --feature patient-intake

### Example 3: Semantic maintenance cycle

1. python3 workflow/cli.py semantic-infer --enforce-threshold
2. python3 workflow/cli.py semantic-drift
3. python3 workflow/cli.py semantic-resolve
4. If safe and approved: python3 workflow/cli.py semantic-resolve --apply

### Example 4: Governed release

1. python3 workflow/cli.py semantic-drift
2. python3 workflow/cli.py semantic-infer --enforce-threshold
3. python3 workflow/cli.py semantic-resolve
4. python3 workflow/cli.py validate-suite
5. python3 workflow/cli.py visualize-all
6. python3 workflow/cli.py sync-all
7. python3 workflow/cli.py ai-export
8. python3 workflow/cli.py release --bump patch [--approve-semantic-changes]

### Example 5: Evolution preview and governed apply

1. python3 workflow/cli.py evolve-all
2. python3 workflow/cli.py evolve-preview --write
3. Review governance requirements in proposal blocks.
4. Apply only with explicit approvals:
	python3 workflow/cli.py evolve-all --apply --approve-evolution --approve-semantic --approve-structural --approve-sync

### Example 6: Expansion preview and governed apply

1. python3 workflow/cli.py expand-all
2. python3 workflow/cli.py expand-preview --write
3. Review proposal lineage, ontology entries, and integration impact.
4. Apply only with explicit approvals:
	python3 workflow/cli.py expand-all --apply --approve-expansion --approve-semantic --approve-structural --approve-sync

### Example 7: Refactor preview and governed apply

1. python3 workflow/cli.py refactor-all
2. python3 workflow/cli.py refactor-preview --write
3. Review semantic and structural impact in proposal blocks.
4. Apply only with explicit approvals:
	python3 workflow/cli.py refactor-all --apply --approve-refactor --approve-semantic --approve-structural --approve-sync

### Example 8: Unified cycle preview and governed apply

1. python3 workflow/cli.py improve-all
2. python3 workflow/cli.py improve-preview --write
3. Review engine ordering, feature summaries, and aggregated governance requirements.
4. Apply only with explicit approvals:
	python3 workflow/cli.py improve-all --apply --approve-evolution --approve-expansion --approve-refactor --approve-semantic --approve-structural --approve-sync

## Recommended Copilot Prompts

1. Load workflow AI context and explain the semantic state for feature <slug>.
2. Generate a deterministic feature definition using workflow/ai_templates/feature.json and workflow/ai_prompts/new_feature_prompt.txt.
3. Run semantic inference analysis for <slug> and report confidence failures only.
4. Analyze semantic drift for <slug> and summarize exact mismatch reasons.
5. Build a safe conflict resolution plan and identify whether force-unsafe is required.
6. Prepare command sequence to scaffold, sync, validate, and visualize feature <name>.

## VS Code AI Integration Notes

1. Keep this order for AI context bootstrap:
- workflow/ai_hints.json
- workflow/ai_navigation.json
- workflow/semantic_context.json
2. Prefer repository instructions in .github/copilot-instructions.md for behavior constraints.
3. Use workflow prompt pack for deterministic reasoning:
- workflow/ai_prompts/new_feature_prompt.txt
- workflow/ai_prompts/semantic_inference_prompt.txt
- workflow/ai_prompts/drift_analysis_prompt.txt
- workflow/ai_prompts/conflict_resolution_prompt.txt
- workflow/ai_prompts/visualization_prompt.txt
4. Do not bypass CLI mutation paths with manual generation when sync and visualize commands exist.
5. For complete operating behavior, align with workflow/COPILOT_OPERATING_MODEL.md.
