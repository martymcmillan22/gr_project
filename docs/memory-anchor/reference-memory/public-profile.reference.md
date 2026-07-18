# Public-Profile Reference Memory

Use this prompt at the start of a Public-Profile chat:

Scope: Public-Profile only.
Use docs/memory-anchor as reference memory, not full preload.
Load only files directly relevant to Public-Profile and AM tier behavior.
Do not load full memory-anchor unless blocked.
Implement the requested feature first, then load more references only if needed.

Primary references:
- docs/memory-anchor/MLAS/SemanticUtility/AM02-MemoryAnchor/vs-code-ai.memory.md
- docs/memory-anchor/MLAS/SemanticUtility/AM06-SessionEngine/vs-code-ai.session-map.md
- docs/memory-anchor/CONSTITUTION/north-star/north-star.md
- docs/memory-anchor/CONSTITUTION/context-injection-module.md

Guardrails:
- Keep AM and PM rails separated.
- Do not infer missing structure.
- Follow deterministic sequence and existing naming.
