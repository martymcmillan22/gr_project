# Personal-Profile Reference Memory

Use this prompt at the start of a Personal-Profile chat:

Scope: Personal-Profile only.
Use docs/memory-anchor as reference memory, not full preload.
Load only files directly relevant to Personal-Profile and PM tier behavior.
Do not load full memory-anchor unless blocked.
Implement the requested feature first, then load more references only if needed.

Primary references:
- docs/memory-anchor/CPINDCNO/PM02-PersonalMemoryAnchor/personal-memory-anchor.md
- docs/memory-anchor/CPINDCNO/PM06-PersonalSessionMap/personal-session-map.md
- docs/memory-anchor/CPINDCNO/PM01-PersonalIdentityRail/personal-identity-rail.md
- docs/memory-anchor/CPINDCNO/identity-packet-specification.md

Guardrails:
- Keep PM rail isolated from AM rail.
- No cross-rail memory mixing.
- Follow deterministic PM03 to PM12 load chain.
