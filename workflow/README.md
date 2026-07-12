# Workflow Command Center

This directory is the unified command center and canonical source for workflow artifacts used to design and build apps, features, UI flows, backend logic, and schema flows.

## Consolidated Layout

To keep the workflow root minimal while preserving deterministic behavior:

- Keep only `README.md` and executable Python entrypoints at workflow root.
- Store durable metadata and AI context files in `workflow/meta`.
- Store generated runtime artifacts in `workflow/reports`.
- Store detailed reference docs in `workflow/meta/docs`.

## Categories

1. database_design/mermaid_erds
2. logic_design/mermaid_sequences
3. ui_templates/penpot_templates
4. ui_components/penpot_components

## Source Mapping (Hard-Moved)

### database_design/mermaid_erds
- docs/architecture/data_schema.mmd
- docs/architecture/mermaid/ERD.txt
- flow_diagram/seed_creator.drawio

### logic_design/mermaid_sequences
- docs/architecture/logic_flow.mmd
- docs/architecture/mermaid/sequence_diagram.txt
- docs/MMD_workflow_guide.txt

### ui_templates/penpot_templates
- ui_template_library/react_onepager/src/layout/AppShell.tsx
- ui_template_library/react_onepager/src/sections/*
- ui_template_library/react_onepager/src/theme.css
- ui_template_library/react_onepager/src/index.ts

### ui_components/penpot_components
- components/ui/*
- components/grassroots/*
- design-system/tokens-penpot-export.json
- design-system/PENPOT_SOURCE.md

## Reorganization Mode

Phase 2 hard move is active. The mapped source artifacts were relocated into workflow/ and old canonical locations were retired.

## Phase-3 Engine MVP

The workflow automation engine lives in workflow/_engine and is exposed by workflow/cli.py.

### Commands

- python workflow/cli.py new-feature --name "Feature Name" --mlas-tier "TierName" --btif-classification "ClassName" --semantic-intent "IntentName" --semantic-tags tag1 tag2
- python workflow/cli.py validate
- python workflow/cli.py validate-suite
- python workflow/cli.py classify
- python workflow/cli.py semantic-check
- python workflow/cli.py sync --feature <slug>
- python workflow/cli.py sync-all
- python workflow/cli.py visualize --feature <slug>
- python workflow/cli.py visualize-all
- python workflow/cli.py semantic-drift
- python workflow/cli.py semantic-infer
- python workflow/cli.py semantic-resolve [--apply]
- python workflow/cli.py semantic-health
- python workflow/cli.py semantic-drift-forecast
- python workflow/cli.py semantic-scorecard
- python workflow/cli.py semantic-strategy-report
- python workflow/cli.py semantic-health --profile quarterly
- python workflow/cli.py semantic-scorecard --profile quarterly --min-confidence 0.85
- python workflow/cli.py semantic-strategy-report --profile quarterly --period YYYY-QN
- python workflow/cli.py semantic-health --profile annual
- python workflow/cli.py semantic-drift-forecast --profile annual --horizon-months 12
- python workflow/cli.py semantic-scorecard --profile annual --min-confidence 0.85
- python workflow/cli.py semantic-strategy-report --profile annual --period YYYY
- python workflow/cli.py semantic-infer --enforce-threshold --min-confidence 0.85
- python workflow/cli.py semantic-resolve --apply [--force-unsafe]
- python workflow/cli.py ai-context
- python workflow/cli.py ai-export
- python workflow/cli.py ai-new-feature --name "Feature Name" [--sync]
- python workflow/cli.py version
- python workflow/cli.py bump-version --part patch
- python workflow/cli.py release --bump patch
- python workflow/cli.py release-notes
- python workflow/cli.py evolve-feature --feature <slug>
- python workflow/cli.py evolve-all
- python workflow/cli.py evolve-preview
- python workflow/cli.py expand [--target <slug>]
- python workflow/cli.py expand-all
- python workflow/cli.py expand-preview
- python workflow/cli.py refactor-feature --feature <slug>
- python workflow/cli.py refactor-all
- python workflow/cli.py refactor-preview
- python workflow/cli.py improve-feature --feature <slug>
- python workflow/cli.py improve-all
- python workflow/cli.py improve-preview
- python3 -m unittest discover workflow/tests -v

### Strict Mode Workflow

Create a Strict Mode QPU workflow:

python workflow/cli.py strict-mode \
	--name "QPU Strict Mode" \
	--inverse-pairs "red:green" "blue:yellow" \
	--relay-segment "red blue yellow green" \
	--srl-values 4 16 64 256 \
	--tenses past present-past present-future future \
	--btif-subjects Math Language Arts Science \
	--semantic-tags strict qpu relay inverse temporal

This command constructs a 4-node Strict Mode workflow:

1. Inverse Pair Assembly
2. Linear Relay Alignment
3. SRL Scaling
4. Temporal Mapping

Each node enforces deterministic rules and throws a Strict Mode error if violated.

### Generated Outputs for new-feature

- workflow/database_design/mermaid_erds/<slug>.erd.mmd
- workflow/logic_design/mermaid_sequences/<slug>.sequence.mmd
- workflow/ui_templates/penpot_templates/features/<slug>/template.md
- workflow/ui_components/penpot_components/features/<slug>/component.md

### Metadata Source of Truth

Feature metadata is stored in workflow/meta/registry.json and validated with workflow/cli.py validate.

## Phase-3 Slice 3: Semantic Integration

Semantic integration modules:

- workflow/_engine/mlas_integration.py
- workflow/_engine/btif_router.py

Semantic checks enforce deterministic consistency for:

- semantic_intent
- semantic_tags
- mlas_tier
- btif_classification

## Phase-3 Slice 4: Sync Layer + Semantic Propagation

Sync modules:

- workflow/_engine/sync_erd.py
- workflow/_engine/sync_sequence.py
- workflow/_engine/sync_ui_template.py
- workflow/_engine/sync_ui_component.py
- workflow/_engine/semantic_propagation.py

Sync behavior:

- ERD to backend model stubs under platform_core/workflow_generated/models/
- sequence to backend logic stubs under platform_core/workflow_generated/logic/
- UI templates to React pages under ui_apps/workflow_generated/pages/
- UI component specs to generated design-system components under workflow/ui_components/penpot_components/generated/

Semantic propagation behavior:

- normalizes semantic_tags
- updates propagation.mlas report for each feature
- updates propagation.btif_route
- records propagation.synced_targets

## Phase-4 Slice 2: Workflow Visualization Layer

Visualization module:

- workflow/_engine/visualize.py

CLI commands:

- python workflow/cli.py visualize --feature <slug>
- python workflow/cli.py visualize-all

Generated visual outputs:

- workflow/visualizations/features/<slug>.visualization.md
- workflow/visualizations/feature-dependency-graph.mmd
- workflow/visualizations/mlas-tier-map.mmd
- workflow/visualizations/btif-routing-map.mmd

## Phase-4 Slice 3: Semantic Engine Deep Integration

Semantic intelligence modules:

- workflow/_engine/semantic_drift.py
- workflow/_engine/semantic_infer.py
- workflow/_engine/semantic_conflicts.py

New semantic commands:

- python workflow/cli.py semantic-drift
- python workflow/cli.py semantic-infer
- python workflow/cli.py semantic-resolve [--apply]

Additional docs:

- workflow/meta/docs/SEMANTIC_DRIFT_OVERVIEW.md
- workflow/meta/docs/SEMANTIC_INFERENCE_OVERVIEW.md

## Phase-4 Slice 4: Semantic Hardening

Hardening policies:

- inference confidence threshold gate via `--enforce-threshold`
- configurable threshold via `--min-confidence`
- autofix safety gate that blocks `--apply` when unsafe conflict types are present
- explicit override via `--force-unsafe`

Test suite:

- workflow/tests/test_semantic_infer.py
- workflow/tests/test_semantic_conflicts.py

## Phase-4 Slice 5: AI-Native Integration

AI onboarding and command files:

- workflow/meta/ai_hints.json
- workflow/meta/ai_navigation.json
- workflow/meta/semantic_context.json

AI prompt surface:

- workflow/ai_prompts/new_feature_prompt.txt
- workflow/ai_prompts/semantic_inference_prompt.txt
- workflow/ai_prompts/drift_analysis_prompt.txt
- workflow/ai_prompts/conflict_resolution_prompt.txt
- workflow/ai_prompts/visualization_prompt.txt

AI template surface:

- workflow/ai_templates/feature.json

AI-native CLI commands:

- python workflow/cli.py ai-context
- python workflow/cli.py ai-export
- python workflow/cli.py ai-new-feature --name "Feature Name" [--sync]

AI integration docs:

- workflow/meta/docs/COPILOT_INTEGRATION_GUIDE.md
- workflow/meta/docs/COPILOT_OPERATING_MODEL.md

## Phase-4 Slice 6: Release And Governance System

Versioning and governance files:

- workflow/meta/version.json
- workflow/meta/governance_policy.json
- workflow/meta/semantic_changelog.md

Release pipeline scripts:

- workflow/release.py
- workflow/release_notes.py

Release docs:

- workflow/meta/docs/RELEASE_OVERVIEW.md
- workflow/meta/docs/VERSIONING_GUIDE.md

Release and version CLI commands:

- python3 workflow/cli.py version
- python3 workflow/cli.py bump-version --part major|minor|patch
- python3 workflow/cli.py release --bump patch [--approve-semantic-changes]
- python3 workflow/cli.py release-notes

Release safety checks:

- semantic-drift must pass
- semantic-infer confidence policy must pass
- semantic-resolve must pass
- validate-suite must pass
- visualize-all must pass
- sync-all must pass
- ai-export must pass

## Phase-5 Slice 1: Semantic Evolution Engine

Evolution engine module:

- workflow/semantic_evolution.py

Long-term evolution governance:

- workflow/meta/governance_long_term.json

Evolution AI surfaces:

- workflow/ai_prompts/ai_evolution_prompt.txt
- workflow/meta/ai_evolution.json

Evolution docs:

- workflow/meta/docs/SEMANTIC_EVOLUTION_OVERVIEW.md

Evolution commands:

- python3 workflow/cli.py evolve-feature --feature <slug>
- python3 workflow/cli.py evolve-all
- python3 workflow/cli.py evolve-preview

Apply mode remains blocked by default unless explicit approvals are provided.

## Phase-5 Slice 2: Semantic Expansion Engine

Expansion engine module:

- workflow/feature_expansion.py

Expansion AI surfaces:

- workflow/ai_prompts/ai_expansion_prompt.txt
- workflow/meta/ai_expansion.json

Expansion docs:

- workflow/meta/docs/FEATURE_EXPANSION_OVERVIEW.md

Expansion commands:

- python3 workflow/cli.py expand [--target <slug>]
- python3 workflow/cli.py expand-all
- python3 workflow/cli.py expand-preview

Expansion apply mode requires explicit approvals:

- --approve-expansion
- --approve-semantic
- --approve-structural
- --approve-sync

## Phase-5 Slice 3: Semantic Refactoring Engine

Refactor engine module:

- workflow/semantic_refactor.py

Refactor AI surfaces:

- workflow/ai_prompts/ai_refactor_prompt.txt
- workflow/meta/ai_refactor.json

Refactor docs:

- workflow/meta/docs/SEMANTIC_REFACTORING_OVERVIEW.md

Refactor commands:

- python3 workflow/cli.py refactor-feature --feature <slug>
- python3 workflow/cli.py refactor-all
- python3 workflow/cli.py refactor-preview

Refactor apply mode requires explicit approvals:

- --approve-refactor
- --approve-semantic
- --approve-structural
- --approve-sync

## Phase-5 Slice 4: Unified Semantic Improvement Cycle

Improvement cycle engine module:

- workflow/semantic_improvement_cycle.py

Improvement cycle AI surfaces:

- workflow/ai_prompts/ai_cycle_prompt.txt
- workflow/meta/ai_cycle.json

Improvement cycle docs:

- workflow/meta/docs/SEMANTIC_IMPROVEMENT_CYCLE_OVERVIEW.md

Improvement cycle commands:

- python3 workflow/cli.py improve-feature --feature <slug>
- python3 workflow/cli.py improve-all
- python3 workflow/cli.py improve-preview

Apply mode requires explicit approvals:

- --approve-evolution
- --approve-expansion
- --approve-refactor
- --approve-semantic
- --approve-structural
- --approve-sync

## Weekly Semantic Health Ritual

Run this deterministic maintenance cycle once per week.

### Monday: Semantic Health Baseline

- python3 workflow/cli.py semantic-health

Output:

- workflow/reports/semantic_health_report.json

### Tuesday: Unified Improvement Planning

- python3 workflow/cli.py improve-all

Output:

- workflow/reports/cycle_plan.json

### Wednesday: Human + AI Review

Review these artifacts before any apply-mode mutation:

- workflow/reports/cycle_plan.json
- per-feature summaries inside cycle plan
- aggregated governance blocks inside cycle plan

### Thursday: Governance Approval Gate

Use explicit approvals for apply mode:

- --approve-evolution
- --approve-expansion
- --approve-refactor
- --approve-semantic
- --approve-structural
- --approve-sync

### Friday Morning: Apply Improvements

- python3 workflow/cli.py improve-all --apply --approve-evolution --approve-expansion --approve-refactor --approve-semantic --approve-structural --approve-sync

### Friday Afternoon: Integrity Chain

- python3 workflow/cli.py validate-suite
- python3 workflow/cli.py visualize-all
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py ai-export
- python3 -m unittest discover workflow/tests -v

### Friday Evening: Release

- python3 workflow/cli.py release --bump patch
- python3 workflow/cli.py release-notes

### Saturday: AI Context Refresh

AI surfaces pick up refreshed outputs from ai-export, including:

- workflow/meta/ai_hints.json
- workflow/meta/ai_navigation.json
- workflow/meta/semantic_context.json
- workflow/meta/ai_cycle.json

## Monthly Semantic Governance Ritual

Run this strategic governance cycle once per month.

### Week 1: Deep Semantic Health Scan

- python3 workflow/cli.py semantic-health --profile monthly

Output:

- workflow/reports/semantic_health_report.json

### Week 1: Full Unified Improvement Cycle

- python3 workflow/cli.py improve-all

Output:

- workflow/reports/cycle_plan.json

### Week 2: Semantic Scorecard Review

- python3 workflow/cli.py semantic-scorecard

Output:

- workflow/reports/semantic_scorecard.json

Council review focus:

- semantic consistency
- structural consistency
- ontology health
- MLAS and BTIF alignment
- intent coverage
- tag ontology clarity
- drift risk
- AI context alignment

### Week 2: Ontology and MLAS BTIF Evolution Review

Council decisions are tracked as:

- approve
- reject
- defer
- request revision

### Week 3: Governance Approval Gate

Apply mode approvals remain explicit:

- --approve-evolution
- --approve-expansion
- --approve-refactor
- --approve-semantic
- --approve-structural
- --approve-sync

### Week 3: Apply Governed Changes

- python3 workflow/cli.py improve-all --apply --approve-evolution --approve-expansion --approve-refactor --approve-semantic --approve-structural --approve-sync

### Week 4: Full Validation Chain

- python3 workflow/cli.py validate-suite
- python3 workflow/cli.py visualize-all
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py ai-export
- python3 -m unittest discover workflow/tests -v

### Week 4: Publish Monthly Semantic Strategy Report

- python3 workflow/cli.py semantic-strategy-report --period YYYY-MM

Output:

- workflow/reports/monthly_semantic_strategy_report.json

### Quarter End Alignment

When the month closes a quarter:

- python3 workflow/cli.py release --bump patch
- python3 workflow/cli.py release-notes

## Quarterly Semantic Release Ritual

Run this platform-wide governed release cycle once per quarter.

### Week 1: Quarterly Deep Semantic Scan

- python3 workflow/cli.py semantic-health --profile quarterly

Output:

- workflow/reports/semantic_health_report_quarterly.json

### Week 1: Quarterly Unified Improvement Cycle

- python3 workflow/cli.py improve-all --profile quarterly

Output:

- workflow/reports/cycle_plan_quarterly.json

### Week 2: Quarterly Semantic Scorecard

- python3 workflow/cli.py semantic-scorecard --profile quarterly --min-confidence 0.85

Output:

- workflow/reports/semantic_scorecard_quarterly.json

### Week 2: Ontology and MLAS BTIF Evolution Planning

Council decision states:

- approve
- reject
- defer
- request revision

### Week 3: Cross-Feature Architecture Planning

Review focus:

- cross-feature integration proposals
- multi-feature bundle proposals
- dependency graph improvements
- semantic intent expansion
- MLAS and BTIF lineage restructuring
- ontology restructuring

### Week 3: Governance Approval and Apply

- python3 workflow/cli.py improve-all --profile quarterly --apply --approve-evolution --approve-expansion --approve-refactor --approve-semantic --approve-structural --approve-sync

### Week 4: Full Validation Chain

- python3 workflow/cli.py validate-suite
- python3 workflow/cli.py visualize-all
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py ai-export
- python3 -m unittest discover workflow/tests -v

### Week 4: Quarterly Semantic Strategy Report

- python3 workflow/cli.py semantic-strategy-report --profile quarterly --period YYYY-QN --quarterly-alignment

Output:

- workflow/reports/quarterly_semantic_strategy_report.json

### Week 4: Quarterly Release and AI Regeneration

- python3 workflow/cli.py release --bump patch
- python3 workflow/cli.py release-notes
- python3 workflow/cli.py ai-export

## Annual Semantic Roadmap Ritual

Run this long-range semantic strategy cycle once per year.

### January: Annual Deep Semantic Scan

- python3 workflow/cli.py semantic-health --profile annual

Output:

- workflow/reports/semantic_health_report_annual.json

### January: Annual Semantic Scorecard

- python3 workflow/cli.py semantic-scorecard --profile annual --min-confidence 0.85

Output:

- workflow/reports/semantic_scorecard_annual.json

### February: Annual Semantic Drift Forecast

- python3 workflow/cli.py semantic-drift-forecast --profile annual --horizon-months 12

Output:

- workflow/reports/annual_semantic_drift_forecast.json

### February: Ontology and MLAS BTIF Long-Range Planning

Council decision states:

- approve
- reject
- defer
- request revision

### March: Annual Semantic Architecture Planning

Define goals for:

- ontology evolution
- MLAS and BTIF tier evolution
- semantic intent evolution
- tag ontology evolution
- dependency graph health
- AI context alignment

### March: Annual Governance Approval and Apply

- python3 workflow/cli.py improve-all --profile annual --apply --approve-evolution --approve-expansion --approve-refactor --approve-semantic --approve-structural --approve-sync
- python3 workflow/cli.py semantic-strategy-report --profile annual --period YYYY

Output:

- workflow/reports/cycle_plan_annual.json
- workflow/reports/annual_semantic_strategy_report.json

### April: Annual Full Validation Chain

- python3 workflow/cli.py validate-suite
- python3 workflow/cli.py visualize-all
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py ai-export
- python3 -m unittest discover workflow/tests -v

### May: Annual Semantic Release and AI Regeneration

- python3 workflow/cli.py release --bump patch
- python3 workflow/cli.py release-notes
- python3 workflow/cli.py ai-export
