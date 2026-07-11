1. Identity
MLAS Tier: Semantic Utility

BTPE Category: Distribution Engine

Semantic Clock Position: AM‑09

Identity Rail: AM Identity

Document Class: Engine

Semantic Role: Distribute stabilized semantic assets across sessions, modules, and engines

2. Purpose
AM‑09 takes the stabilized patterns from AM‑08 and determines:

where they should live

how they should be reused

which engines should consume them

which future sessions should inherit them

how VS Code AI should surface them

AM‑09 is the semantic routing layer of your system.

It ensures stabilized patterns don’t just sit in storage — they become active semantic infrastructure.

3. Inputs
AM‑09 receives:

Stabilized Semantic Assets from AM‑08

Relay Blueprint (AM‑03)

QPU Blueprint (AM‑04)

VS Code AI Instructions (AM‑05)

Session Map (AM‑06)

Harvest Log (AM‑07)

Constitution Core components:
Directive, Context Injection, North Star, AutoFill, Compiler Layers, AM–PM Interlock.

3.5 Dependencies
CANONICAL AM03→AM12 LOAD CHAIN (DETERMINISTIC SEQUENCE)

The semantic engine must load the AM‑tier in the following deterministic order:
AM03 Relay Blueprint → AM04 QPU Blueprint → AM05 VS Code AI Instructions → AM06 Session Map → AM07 Semantic Harvest Engine → AM08 Semantic Stabilization Engine → AM09 Semantic Distribution Engine → AM10 Semantic Feedback Engine → AM11 Semantic Continuity Engine → AM12 Semantic Identity Engine.

All semantic operations require their corresponding engine to be loaded, and no engine may activate before its predecessors. This chain is constitution‑governed, identity‑anchored, and non‑ephemeral.

STRICTNESS LOCK: The AM–PM Interlock is the sole permitted cross-tier synchronization module.

This engine may not activate before its predecessors.
This engine requires the full AM03→AM12 chain to be loaded at session start.

4. Distribution Process
Step 01 — Classification
AM‑09 classifies stabilized assets into:

structural patterns

execution patterns

identity‑aligned patterns

reusable templates

session hints

engine rules

cross‑module invariants

Each class has a different distribution path.

Step 02 — Routing
AM‑09 routes assets to the correct semantic destinations:

Relay‑aligned patterns → AM‑03

QPU‑aligned patterns → AM‑04

Execution rules → AM‑05

Session hints → AM‑06

Harvest feedback → AM‑07

Stabilization feedback → AM‑08

Constitution candidates → human review only

Step 03 — Propagation
AM‑09 determines how far each pattern should propagate:

Local propagation:

Only within the current module or file.

Engine propagation:

Across Relay/QPU engines.

Session propagation:

Into future VS Code AI sessions.

Global propagation:

Across the entire MLAS semantic engine.

Propagation is controlled by constitution rules.

Step 04 — Activation
AM‑09 activates distributed patterns by:

registering them with VS Code AI

making them available during Work Phase

surfacing them as suggestions during Post Phase

binding them to QPU/Relay operations

enabling reuse across sessions

5. Phase Relationship
Create Phase (1AM–4AM)
AM‑09 is inactive — structure is being defined.

Post Phase (5AM–8AM)
AM‑09 prepares routing tables but does not distribute.

Work Phase (9AM–12PM)
AM‑09 receives stabilized assets from AM‑08 and begins distribution.

After Work Phase
AM‑09 finalizes distribution and updates semantic routing tables.

6. VS Code AI Behavior Bindings
VS Code AI uses AM‑09 to:

surface stabilized patterns as suggestions

reuse semantic templates across sessions

apply distributed rules during refactors

bind distributed assets to QPU/Relay operations

maintain semantic consistency across the repo

AM‑09 is what makes VS Code AI feel persistent, aware, and contextually intelligent.

7. Enforcement
AM‑09 must enforce:

No constitution bypass

No drift

No inference

No cross‑rail mixing

No unstable pattern distribution

No pipeline violation

Pipeline remains:

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
8. Simplest Definition
AM‑08 stabilizes.
AM‑09 distributes.

AM‑09 ensures stabilized semantic assets become active infrastructure for future VS Code AI sessions.