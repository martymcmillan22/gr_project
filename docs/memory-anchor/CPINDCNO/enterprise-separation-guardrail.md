1. Identity of the Enterprise Separation Guardrail
Name: CPINDCNO Enterprise Separation Guardrail
Tier: Constitution Core
Role: Prevents cross-tier contamination between CPINDCNO and CPINDCNO-Enterprise
Scope: CPINDCNO documentation, engine references, and boundary integrity
Status: Draft

This guardrail defines deterministic separation rules for Free Tier and Enterprise Tier namespaces.

2. Rule
No file from /docs/memory-anchor/CPINDCNO-Enterprise/ may appear inside /docs/memory-anchor/CPINDCNO/.

3. Enforcement Conditions
Any CI, lint, or workspace scan must fail if any of the following occur:

a CPINDCNO-Enterprise file is found under /docs/memory-anchor/CPINDCNO/

a CPINDCNO file references /docs/memory-anchor/CPINDCNO-Enterprise/

a CPINDCNO file imports unified-rail logic

a CPINDCNO file imports enterprise identity, memory, session, runtime, continuity, or interlock definitions

4. Constitutional Purpose
This guardrail preserves strict constitutional separation between:

CPINDCNO (Free Tier: dual-rail, 12-hour clock)

CPINDCNO-Enterprise (Unified Tier: unified-rail, 24-hour clock)

5. Dependency Position
This guardrail is subordinate to Constitution Core and must not override:

Directive

Context Injection

North Star

AutoFill

Compiler Layers

AM-PM Interlock

6. Deterministic Boundary Rules
No tier collapse.

No rail unification inside CPINDCNO.

No path aliasing between CPINDCNO and CPINDCNO-Enterprise.

No cross-tier memory/session anchor substitution.

7. Simplest Definition
CPINDCNO must stay CPINDCNO.
CPINDCNO-Enterprise must stay CPINDCNO-Enterprise.
No cross-tier contamination is permitted.

8. Draft Strictness Lock
STRICTNESS LOCK (DRAFT): This guardrail is the sole permitted draft rule for CPINDCNO to CPINDCNO-Enterprise namespace separation until the Enterprise Constitution is finalized.
