Semantic Harvest Engine — AM‑07

1. Engine identity

MLAS Tier: Semantic Utility

BTPE Category: Semantic Harvest Engine

Semantic Clock Position: AM‑07

Identity Rail: AM Identity

Document Class: Engine

Semantic Role: Collect, aggregate, and stabilize semantic output from Work Phase operations
2. Purpose
Primary function:

Turn Relay‑scale work (fine edits, term/meta‑term changes) into stable, reusable semantic assets.

Scope:

Operates over Work Phase output (9AM–12PM).

Aggregates changes made via QPU decomposition → Relays.

Produces harvested artifacts: patterns, invariants, reusable structures.

3. Inputs
From AM‑03:

repository-relay.blueprint.md — structural grid (1–4–16–64–85).

From AM‑04:

qpu.blueprint.md — execution grid (4–16–64–256–340).

From AM‑05:

vs-code-ai.instructions.md — orchestration rules.

From AM‑06:

vs-code-ai.session-map.md — session flow and phase behavior.

From Constitution Core:

Directive, Context Injection, North Star, AutoFill, Compiler Layers, AM–PM Interlock.

From Work Phase:

Relay‑scale edits, refactors, term/meta‑term changes, semantic decisions.

3.5 Dependencies
CANONICAL AM03→AM12 LOAD CHAIN (DETERMINISTIC SEQUENCE)

The semantic engine must load the AM‑tier in the following deterministic order:
AM03 Relay Blueprint → AM04 QPU Blueprint → AM05 VS Code AI Instructions → AM06 Session Map → AM07 Semantic Harvest Engine → AM08 Semantic Stabilization Engine → AM09 Semantic Distribution Engine → AM10 Semantic Feedback Engine → AM11 Semantic Continuity Engine → AM12 Semantic Identity Engine.

All semantic operations require their corresponding engine to be loaded, and no engine may activate before its predecessors. This chain is constitution‑governed, identity‑anchored, and non‑ephemeral.

STRICTNESS LOCK: The AM–PM Interlock is the sole permitted cross-tier synchronization module.

This engine may not activate before its predecessors.
This engine requires the full AM03→AM12 chain to be loaded at session start.

4. Harvest process
Step 01 — Collect:

Gather all Relay‑scale changes produced during the session.

Step 02 — Group:

Cluster changes by:

subject

branch

term

meta‑term

QPU origin

Step 03 — Evaluate:

Identify which changes are:

stable patterns

one‑off fixes

emergent structures

constitutional candidates

Step 04 — Promote:

Promote stable patterns into:

reusable templates

engine rules

constitution amendments (only via explicit human approval).

Step 05 — Record:

Write harvested patterns into:

semantic pattern docs

engine configuration

future session hints (non‑ephemeral guidance).

5. Phase relationship
Create Phase:

Defines Relay/QPU structure; harvest engine is inactive.

Post Phase:

QPU multiplication; harvest engine observes but does not commit.

Work Phase:

QPU decomposition → Relay; harvest engine actively collects and stabilizes output.

After Work Phase:

Harvest engine finalizes patterns and prepares them for reuse in future sessions.

6. VS Code AI behavior bindings
During Work Phase:

VS Code AI tags edits with:

Relay ID

QPU origin

phase/compartment

These tags feed the harvest engine.

At session end:

VS Code AI triggers a harvest pass:

summarize changes

identify patterns

propose promotions (e.g., “this refactor looks like a reusable pattern”).

7. Enforcement
No auto‑constitution changes:

Harvest engine may suggest, but not directly modify, constitutional files.

No pattern drift:

Harvested patterns must match Relay/QPU blueprints.

No phase confusion:

Only Work Phase output is eligible for harvest.

No pipeline violation:

Harvested artifacts must respect:

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