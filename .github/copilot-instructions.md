# Copilot Instructions For Grassroots

Use GRASSROOTS_AI_WORKFLOW.md in this repository as the authoritative workflow directive for all tasks.

Required behavior for this repo:
- Follow Penpot to MDX to React to MLAS BTIF pipeline in order.
- Do not generate JSX from screenshots or images.
- Do not infer layout from graphics.
- Generate code only from explicit structural instructions.
- Keep naming deterministic and consistent across Penpot, MDX, React, and MLAS BTIF.
- Prefer incremental edits and confirm assumptions when structure is missing.

When conflicts arise, prefer the stricter deterministic constraint.

This project uses a deterministic semantic pipeline.
All tasks must apply the Grassroots directive unless explicitly told otherwise.

## AI-Native Workflow Operating Model

For workflow platform tasks, always bootstrap context by reading:

- workflow/meta/ai_hints.json
- workflow/meta/ai_navigation.json
- workflow/meta/semantic_context.json

Command-first mutation policy for workflow/:

- Prefer python3 workflow/cli.py commands for all state mutations.
- Do not edit workflow/meta/registry.json directly when a CLI command exists.
- Use ai-new-feature or new-feature for feature creation.
- Use sync/sync-all for generated output updates.
- Use visualize/visualize-all for diagram outputs.

Safety policy:

- Respect semantic inference confidence thresholds.
- Respect semantic conflict safety gates.
- Never use semantic-resolve --force-unsafe unless user explicitly requests unsafe override.

AI prompt/template usage for workflow generation and reasoning:

- workflow/ai_templates/feature.json
- workflow/ai_prompts/new_feature_prompt.txt
- workflow/ai_prompts/semantic_inference_prompt.txt
- workflow/ai_prompts/drift_analysis_prompt.txt
- workflow/ai_prompts/conflict_resolution_prompt.txt
- workflow/ai_prompts/visualization_prompt.txt
- workflow/ai_prompts/ai_evolution_prompt.txt
- workflow/ai_prompts/ai_expansion_prompt.txt
- workflow/ai_prompts/ai_refactor_prompt.txt
- workflow/ai_prompts/ai_cycle_prompt.txt

Long-term evolution governance:

- workflow/meta/governance_long_term.json

Detailed playbook:

- workflow/meta/docs/COPILOT_OPERATING_MODEL.md
- workflow/meta/docs/COPILOT_INTEGRATION_GUIDE.md
