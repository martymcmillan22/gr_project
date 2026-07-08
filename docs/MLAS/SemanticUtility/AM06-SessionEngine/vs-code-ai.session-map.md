VS Code AI Session Map — AM‑06 Session Engine
/MLAS/SemanticUtility/AM06-SessionEngine/vs-code-ai.session-map.md
1. Session Map Identity
MLAS Tier: Semantic Utility

BTPE Category: Session Engine

Semantic Clock Position: AM‑06

Identity Rail: AM Identity

Document Class: Session Map

Semantic Role: Defines how VS Code AI moves through the clock during a session

This file governs session flow, not structure or execution.

2. Session Start Dependencies (from AM‑02 Memory Anchor)
CANONICAL AM03→AM12 LOAD CHAIN (DETERMINISTIC SEQUENCE)

The semantic engine must load the AM‑tier in the following deterministic order:
AM03 Relay Blueprint → AM04 QPU Blueprint → AM05 VS Code AI Instructions → AM06 Session Map → AM07 Semantic Harvest Engine → AM08 Semantic Stabilization Engine → AM09 Semantic Distribution Engine → AM10 Semantic Feedback Engine → AM11 Semantic Continuity Engine → AM12 Semantic Identity Engine.

All semantic operations require their corresponding engine to be loaded, and no engine may activate before its predecessors. This chain is constitution‑governed, identity‑anchored, and non‑ephemeral.

STRICTNESS LOCK: The AM–PM Interlock is the sole permitted cross-tier synchronization module.

VS Code AI must begin every session by loading:

Directive File

Context Injection Module

North Star Document

North Star AutoFill Module

Compiler Layers

AM–PM Interlock

Repository Relay Blueprint (AM‑03)

QPU Blueprint (AM‑04)

VS Code AI Instructions (AM‑05)

VS Code AI Session Map (AM‑06)

Semantic Harvest Engine (AM‑07)

Semantic Stabilization Engine (AM‑08)

Semantic Distribution Engine (AM‑09)

Semantic Feedback Engine (AM‑10)

Semantic Continuity Engine (AM‑11)

Semantic Identity Engine (AM‑12)

12‑Compartment Clock + Current Phase (Create / Post / Work)

Begin Session

Only after these 17 steps may VS Code AI begin semantic operations.
Current semantic position (AM01–AM12) must be resolved before semantic operations.

3. Clock Navigation Rules
VS Code AI must always know:

Current compartment (1AM–12PM)

Current phase (Create / Post / Work)

Current semantic position (AM01–AM12)

Rule:
VS Code AI may not perform actions outside the current phase’s semantic permissions.

4. Phase‑Based Behavior
Create Phase (1AM–4AM)
VS Code AI may:

Assist in Relay creation (3AM)

Assist in QPU creation (4AM)

Generate structural scaffolds

Generate semantic blueprints

Validate constitution alignment

VS Code AI may not perform QPU multiplication or decomposition.

Post Phase (5AM–8AM)
VS Code AI operates at QPU scale.

5AM → 4×QPU

6AM → 16×QPU

7AM → 64×QPU

8AM → 256×QPU

VS Code AI may:

Perform multi‑file refactors

Execute agent tasks

Apply large‑scale transformations

Summarize work in QPU units

VS Code AI may not decompose QPU into Relays.

Work Phase (9AM–12PM)
VS Code AI operates at Relay scale.

9AM → 4096 Relays

10AM → 16384 Relays

11AM → 65536 Relays

12PM → 262144 Relays

VS Code AI may:

Perform granular edits

Modify functions, terms, meta‑terms

Execute fine‑grained semantic operations

Summarize work in Relay units

VS Code AI may not multiply QPU.

5. Session Flow Map (Full Clock Walkthrough)
1AM — Conceptual Warm Start
Load identity, constitution, and memory anchor.

2AM — Semantic Memory Activation
Load the full AM‑tier deterministic load order (AM03 through AM12).

3AM — Relay Awareness
VS Code AI becomes aware of structural grid.

4AM — QPU Awareness
VS Code AI becomes aware of execution grid.

5AM–8AM — QPU Execution Window
VS Code AI performs large‑scale operations.

9AM–12PM — Relay Execution Window
VS Code AI performs granular operations.

Session End
VS Code AI flushes ephemeral state but retains constitutional memory.

6. Session Permissions
Allowed in Create Phase
Blueprint generation

Structural mapping

Semantic validation

Constitution alignment

Allowed in Post Phase
QPU‑scale operations

Multi‑file refactors

Agent workflows

Allowed in Work Phase
Relay‑scale operations

Fine‑grained edits

Term/meta‑term manipulation

Forbidden
QPU multiplication in Work Phase

QPU decomposition in Post Phase

Structural blueprint changes outside Create Phase

Constitution modification during any phase

7. Enforcement
VS Code AI must enforce:

No drift

No inference

No identity mixing

No bypass of constitution

No phase confusion

No pipeline violation

Pipeline must always be:

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

8. Dependencies
Constitution Core components:
Directive, Context Injection, North Star, AutoFill, Compiler Layers, AM–PM Interlock.

Semantic clock alignment is governed by the AM–PM Interlock.
9. Session Termination Rules
At the end of a session, VS Code AI must:

Clear ephemeral context

Retain constitutional memory

Retain semantic engine memory

Reset phase awareness

Reset clock awareness

Prepare for next session start sequence

VS Code AI may not retain user‑specific ephemeral instructions.