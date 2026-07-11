# Semantic Refactoring Overview

## What Refactoring Is

Semantic refactoring is deterministic proposal generation for improving feature structure and semantic coherence without changing business intent.

## Refactor Engine

- workflow/semantic_refactor.py

The refactor engine proposes updates for:

- ERD normalization and redundancy removal
- sequence flow clarity and dead-path cleanup
- UI template and component naming consistency
- semantic metadata normalization (intent, tags)
- MLAS/BTIF lineage alignment
- tag ontology merge/rename/deprecate candidates

## Governance

Refactor governance is defined in:

- workflow/governance_long_term.json

Apply mode requires explicit approvals:

- refactor_approval
- semantic_approval
- structural_approval
- sync_approval

## CLI Commands

- python3 workflow/cli.py refactor-feature --feature <slug>
- python3 workflow/cli.py refactor-all
- python3 workflow/cli.py refactor-preview

Apply examples:

- python3 workflow/cli.py refactor-all --apply --approve-refactor --approve-semantic --approve-structural --approve-sync
- python3 workflow/cli.py refactor-feature --feature pilot-intake --apply --approve-refactor --approve-semantic --approve-structural --approve-sync

Preview example:

- python3 workflow/cli.py refactor-preview --write

## AI Surfaces

- workflow/ai_prompts/ai_refactor_prompt.txt
- workflow/ai_refactor.json
