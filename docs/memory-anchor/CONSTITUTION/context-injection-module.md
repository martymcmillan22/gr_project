# Context Injection Module — BaseTrue Semantic Engine

## Module Identity
- MLAS Tier: Semantic Utility
- BTPE Category: Context Pattern Engine
- Identity Rail: AM Identity
- Semantic Clock Position: AM‑05
- Semantic Role: Context Injection Engine

## Module Purpose
The Context Injection Module defines how VS Code AI must gather, assemble, validate, and inject context before executing any task.  
It binds the Directive File, North Star Document, Repo State, and Task Context into a single deterministic frame.

No context may be inferred.  
No context may bypass MLAS → BTPE → Identity Rail.  
No context may override immutable laws.

---

## Context Inputs
The module reads context from four canonical sources:

### Source 01 — Directive File Context
- BaseTrue Constants  
- Semantic Laws  
- Identity Rails  
- Pipeline Requirements  
- AI Refusal Conditions  

### Source 02 — North Star Context
- Vision Statement  
- Capability Table  
- Semantic Positioning  
- UX Spine  
- Deterministic Rules  
- AutoFill Module  
- Compiler Layer  

### Source 03 — Repo Structural Context
- MDX files  
- React components  
- Routes  
- Semantic metadata  
- Structural scaffolds  

### Source 04 — Task Context
- The current user request  
- The declared target module  
- The declared identity rail  

No other context sources are permitted.

---

## Context Outputs
The module generates deterministic values for:

- Directive Context Frame  
- North Star Context Frame  
- Repo Context Frame  
- Task Context Frame  
- Context Integrity Report  
- Context Refusal Trigger  
- Context Binding Map  
- Context Execution Envelope  

These outputs are consumed by the Context Compiler Layer and the North Star Compiler Layer.

---

## Context Injection Order
Context must be injected in this exact sequence:

1. Directive File Context  
2. North Star Context  
3. Repo Structural Context  
4. Task Context  

No inversion allowed.  
No skipping allowed.  
No partial injection allowed.

---

## Directive File Context Injection
Directive File context must be injected first.

The module loads:

- BaseTrue Constants  
- Semantic Laws  
- Identity Rails  
- Pipeline Requirements  
- AI Refusal Conditions  

If Directive File is missing → **Refuse**.

---

## North Star Context Injection
North Star context must be injected second.

The module loads:

- Vision Statement  
- Capability Table  
- Semantic Positioning  
- UX Spine  
- Deterministic Rules  
- AutoFill Module  
- Compiler Layer  

If North Star is missing → **Refuse auto‑fill** and enter read‑only mode.

---

## Repo Structural Context Injection
Repo context must be injected third.

The module reads:

- MDX structure  
- React components  
- Routes  
- Semantic metadata  
- Structural scaffolds  

The module must **not**:

- infer layout  
- invent components  
- bypass MLAS/BTPE  

If repo context is missing → **Refuse structural tasks**.

---

## Task Context Injection
Task context must be injected last.

The module reads:

- user request  
- target module  
- declared identity rail  
- declared MLAS/BTPE (if provided)  

Task context must be validated against all higher contexts.

If task violates any law → **Refuse**.

---

## Context Integrity Rules
- Rule 01 — Context must be explicit, never inferred.  
- Rule 02 — Context must be deterministic, never probabilistic.  
- Rule 03 — Context must be complete enough to execute.  
- Rule 04 — Context must respect identity rails.  
- Rule 05 — Context must respect the pipeline.  
- Rule 06 — Context must map to MLAS → BTPE → Identity Rail.  
- Rule 07 — Context must never override immutable laws.  

---

## Context Binding Map
Directive Context → Global Semantic Frame  
North Star Context → App/Feature Identity Frame  
Repo Context → Structural Frame  
Task Context → Execution Frame  

Binding must follow:

Directive → North Star → Repo → Task

No lower frame may override a higher frame.

---

## Context Refusal Conditions
The module must refuse when:

- Directive File is missing or contradicted  
- North Star is missing or incomplete  
- MLAS or BTPE are missing  
- Identity Rail is missing or mixed  
- Pipeline is bypassed  
- Semantic drift is requested  
- CPINDC is referenced  
- Immutable laws are challenged  

Refusal must specify **which context layer failed**.

---

## Enforcement
- Enforcement 01 — All tasks begin with Directive File context.  
- Enforcement 02 — No app/feature task may run without North Star.  
- Enforcement 03 — No structural task may run without Repo context.  
- Enforcement 04 — No semantic task may bypass MLAS → BTPE → Identity Rail.  
- Enforcement 05 — All violations must trigger refusal.  

---

## Module Closure
This module is immutable.  
No pipeline substitution allowed.  
No identity rail mixing allowed.  
No semantic drift allowed.  
No autonomous context inference allowed.
