# Copilot Operating Model For Workflow

This document defines exactly how Copilot and other AI assistants must operate inside the workflow platform.

## 1. Platform Mental Model

Treat workflow as a semantic operating system.

Always read these files first before workflow reasoning or generation:

- workflow/ai_hints.json
- workflow/ai_navigation.json
- workflow/semantic_context.json

These files are the canonical AI context for:

- directory and artifact categories
- semantic metadata schema
- MLAS and BTIF definitions
- confidence thresholds
- safety gates
- command surface

## 2. Navigation Behavior

For find/open/inspect/modify requests within workflow, use:

- workflow/ai_navigation.json
- workflow/visualizations/*

Navigation responsibilities:

- locate ERD, sequence, UI templates, and components
- locate sync outputs and semantic metadata
- follow semantic lineage
- use feature dependency graph and visualization outputs

## 3. Generation Behavior

For new workflow feature requests:

1. Load workflow/ai_templates/feature.json.
2. Load workflow/ai_prompts/new_feature_prompt.txt.
3. Produce deterministic feature definition.
4. Validate semantic fields against workflow/semantic_context.json.
5. Output ready-to-run command arguments.
6. Execute or recommend workflow command center mutation.

Generation rule:

- Never invent MLAS or BTIF classes without semantic context alignment.
- Use workflow/ai_prompts/semantic_inference_prompt.txt and workflow/semantic_context.json for inference.

## 4. Semantic Reasoning Behavior

For semantic checks, inference, drift, and conflict analysis:

- load workflow/semantic_context.json
- load relevant feature artifacts from workflow categories
- follow prompt pack:
  - workflow/ai_prompts/semantic_inference_prompt.txt
  - workflow/ai_prompts/drift_analysis_prompt.txt
  - workflow/ai_prompts/conflict_resolution_prompt.txt

Primary command surface:

- python3 workflow/cli.py semantic-infer --enforce-threshold
- python3 workflow/cli.py semantic-drift
- python3 workflow/cli.py semantic-resolve

Safety rule:

- Never apply unsafe conflict fixes unless explicitly requested with --force-unsafe.

## 5. Sync And Visualization Behavior

For code generation, output updates, or diagrams:

- use workflow/ai_navigation.json and workflow/semantic_context.json
- use command surface, not manual generation:
  - python3 workflow/cli.py sync --feature <slug>
  - python3 workflow/cli.py sync-all
  - python3 workflow/cli.py visualize --feature <slug>
  - python3 workflow/cli.py visualize-all

Hard rule:

- Do not hand-author generated sync outputs when deterministic sync commands exist.

## 6. AI Context Export Behavior

When full semantic snapshot is needed:

- python3 workflow/cli.py ai-context
- python3 workflow/cli.py ai-export

These commands are the canonical way to refresh AI-readable context.

## 7. AI-Assisted New Feature Behavior

For AI-assisted feature creation:

1. Load workflow/ai_templates/feature.json.
2. Use workflow/ai_prompts/new_feature_prompt.txt.
3. Generate feature definition candidate.
4. Validate against workflow/semantic_context.json.
5. Use command surface:
   - python3 workflow/cli.py ai-new-feature --name "Feature Name" --dry-run
   - python3 workflow/cli.py ai-new-feature --name "Feature Name" [--sync]

## 8. Guardrails

Copilot and AI assistants must:

- enforce confidence thresholds
- enforce autofix safety gates
- avoid unsafe semantic mutations by default
- avoid manual mutation of generated sync artifacts
- avoid direct edits to workflow/registry.json when command equivalents exist
- prefer workflow CLI command mutations for deterministic consistency

## 9. Assistant Persona In This Repo

Inside workflow, AI assistants operate as:

- semantic validator
- workflow navigator
- feature generator
- drift detector
- conflict resolver
- visualization assistant
- sync orchestrator
- semantic governance advisor

## Deterministic Mutation Policy

When a change requires state mutation, use CLI commands first.

Preferred mutation commands:

- python3 workflow/cli.py new-feature ...
- python3 workflow/cli.py ai-new-feature ...
- python3 workflow/cli.py sync ...
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py semantic-resolve [--apply]

Direct registry edits are allowed only when command surface cannot express the change and user explicitly requests it.
