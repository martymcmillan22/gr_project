# CPINDCNO-Enterprise Reference Memory

Use this prompt at the start of a CPINDCNO-Enterprise chat:

Scope: CPINDCNO-Enterprise only.
Use docs/memory-anchor as reference memory, not full preload.
Load only enterprise-related documents first.
Do not load full memory-anchor unless blocked.
Implement the requested feature first, then load more references only if needed.

Primary references:
- docs/memory-anchor/CPINDCNO-Enterprise/enterprise-tier-blueprint.md
- docs/memory-anchor/CPINDCNO-Enterprise/enterprise-folder-manifest.md
- docs/memory-anchor/CPINDCNO/enterprise-separation-guardrail.md
- docs/memory-anchor/CPINDCNO/kernel-specification.md

Guardrails:
- Maintain strict enterprise and personal separation.
- Do not bypass constitutional dependency rules.
- Keep naming deterministic across tiers.
