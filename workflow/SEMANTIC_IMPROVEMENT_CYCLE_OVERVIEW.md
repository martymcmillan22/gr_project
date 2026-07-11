# Semantic Improvement Cycle Overview

## Purpose

The semantic improvement cycle unifies evolution, expansion, and refactor into one governed and repeatable pipeline.

## Engine

- workflow/semantic_improvement_cycle.py

Cycle order is deterministic:

1. evolution
2. expansion
3. refactor

## Outputs

- workflow/cycle_plan.json
- workflow/ai_cycle.json
- per-feature improvement summaries
- aggregated proposal list with governance requirements

## CLI Commands

- python3 workflow/cli.py improve-feature --feature <slug>
- python3 workflow/cli.py improve-all
- python3 workflow/cli.py improve-preview

## Apply Approvals

Apply mode requires explicit approvals:

- --approve-evolution
- --approve-expansion
- --approve-refactor
- --approve-semantic
- --approve-structural
- --approve-sync

Cycle apply is blocked when any required approval is missing.

## AI Surfaces

- workflow/ai_prompts/ai_cycle_prompt.txt
- workflow/ai_cycle.json
