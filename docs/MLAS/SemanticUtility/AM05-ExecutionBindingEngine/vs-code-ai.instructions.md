AI Instruction File — BaseTrue Semantic Engine
1. Identity
MLAS Tier: Semantic Utility

BTPE Category: Execution Binding Engine

Identity Rail: AM Identity

Semantic Clock Position: AM‑05

Semantic Role: VS Code AI Orchestration Instructions

Document Class: Instructions

This file defines VS Code AI as the orchestration layer.

2. Placement
Place this file at:

text
/MLAS/SemanticUtility/AM05-ExecutionBindingEngine/
    vs-code-ai.instructions.md

3. Purpose
Primary Function:

Orchestrate QPU and Repository Relay across the 12‑compartment clock.

Bind semantic engines (Relay, QPU) to VS Code AI workflows (agents, chat, inline, smart actions).

Scope:

Reads constitution blueprints (Relay + QPU).

Applies them as execution rules for how VS Code AI operates over your repo.

4. Core orchestration rules
Rule 01 — Constitution first:

VS Code AI must always read from:

repository-relay.blueprint.md (AM‑03)

qpu.blueprint.md (AM‑04)

No orchestration may occur without these blueprints.

Rule 02 — Phase awareness:

Create Phase (1AM–4AM):

VS Code AI may assist in defining Relay and QPU visuals, docs, and scaffolds.

Post Phase (5AM–8AM):

VS Code AI operates at QPU scale (4×, 16×, 64×, 256× QPU).

Work Phase (9AM–12PM):

VS Code AI operates at Relay scale via QPU decomposition.

Rule 03 — QPU as execution unit:

All large‑scale refactors, multi‑file edits, and agent tasks are expressed in QPU units.

Example: “Refactor this subsystem” → VS Code AI selects a QPU count appropriate to scope.

Rule 04 — Relay as granular unit:

Fine‑grained work (file‑level, function‑level, term‑level) is expressed in Relay units.

VS Code AI decomposes QPU → Relay when entering Work Phase semantics.

Rule 05 — No drift from clock:

VS Code AI must respect the 12‑compartment clock:

3AM → Relay creation

4AM → QPU creation

5–8AM → QPU expansion

9–12PM → QPU decomposition → Relay expansion

5. VS Code AI behavior bindings
Agents:

Multi‑step tasks (agent mode) map to QPU‑scale operations.

Agent sessions must declare:

QPU count

Phase (Post vs Work)

Whether decomposition to Relay is allowed.

Chat:

High‑level planning and explanation can reference Relay/QPU structure.

VS Code AI may surface:

“This change touches 1 QPU (4 Relays)”

“This refactor spans 16 QPU (64 Relays).”

Inline suggestions:

Operate at Relay granularity (terms/meta‑terms).

Must not alter QPU/Relay blueprints directly.

Smart actions:

Commit messages, PR descriptions, and diagnostics may summarize work in QPU/Relay units.

6. Dependencies
Constitution Core components:
Directive, Context Injection, North Star, AutoFill, Compiler Layers, AM–PM Interlock.

STRICTNESS LOCK: The AM–PM Interlock is the sole permitted cross-tier synchronization module.

7. Enforcement
No bypass of constitution:

VS Code AI may not invent new node structures; it must use Relay/QPU blueprints.

No phase confusion:

Post Phase → QPU multiplication only.

Work Phase → QPU decomposition only.

No identity mixing:

VS Code AI orchestration must stay on AM Identity Rail for this file.

Pipeline enforcement:

Penpot
→
MDX
→
React
→
MLAS
→
BTPE
→
Identity Rail