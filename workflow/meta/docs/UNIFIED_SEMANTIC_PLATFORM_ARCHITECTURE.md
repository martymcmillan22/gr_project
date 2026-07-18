# Unified Semantic Platform Architecture (Canonical v1.0)

## A. System identity

**Platform type:** Semantic operating system  
**Core objective:** Governed semantic production from feature intent to long-range evolution  
**Canonical maps:**
- `workflow/README.md`
- `basetrue/README_BTIF_BTPE.md`
- `basetrue/anchors/bt_anchor.json`

---

## B. Five-layer runtime model

### 1. Workflow Artifact System (Phase 2-3)

**Responsibility:** Deterministic artifact generation and propagation  
**Assets:** ERDs, sequence diagrams, UI templates, UI components, registry, sync, visualization  
**Primary outputs:** Generated artifacts and synced targets  
**Core rule:** Artifact creation must remain reproducible from metadata and semantic inputs.

### 2. Semantic Intelligence Engine (Phase 4)

**Responsibility:** Detect, infer, score, resolve, and report semantic state  
**Capabilities:** Drift detection, inference, conflict handling, health, scorecards, strategy reporting  
**Core rule:** Inference and conflict actions must pass threshold and safety policy before apply mode.

### 3. Governance and Release System (Phase 4-5)

**Responsibility:** Version integrity, approval gating, release safety, cycle governance  
**Capabilities:** Release orchestration, policy enforcement, periodic rituals  
**Core rule:** No semantic mutation without explicit approval flags and passing integrity chain.

### 4. Evolution, Expansion, Refactor Engines (Phase 5)

**Responsibility:** Controlled semantic transformation  
**Capabilities:** Evolve, expand, refactor, improve cycle  
**Core rule:** Transformations are governed mutations, not freeform edits.

### 5. AI-Native Integration Layer

**Responsibility:** AI context ingestion, prompt/template grounding, AI-assisted generation  
**Capabilities:** AI context, export, feature generation, post-release regeneration  
**Core rule:** AI actions stay inside canonical anchors, governance policy, and confidence gates.

---

## C. BaseTrue tier to workflow phase alignment

- **Novice** -> Artifact initiation
- **Intermediate** -> Semantic integration and propagation
- **Studio** -> Deep semantic operation and AI workstation mode
- **Enterprise** -> Governed cross-feature tower execution and long-cycle planning

---

## D. Studio and Enterprise semantic contract

### Studio

- Semantic workstation
- Scaled QPU mode
- No tower floor execution
- Overlay-first behavior

### Enterprise

- Semantic skyscraper
- Tower QPU mode with multi-floor execution
- 4 zones x 4 floors deterministic structure
- Cross-feature orchestration with governance coupling

### Shared deterministic elements

- Monuments -> Checkout -> Surveys -> Polls chain
- Temporal ownership split:
  - QC -> past, present_past
  - QA -> present_future, future
- Garden maintenance execution layer: manufacturing, contractors, logistics, shipping

---

## E. Canonical data plane

- **BaseTrue anchor plane:** `basetrue/anchors/bt_anchor.json`
- **Workflow metadata plane:** `workflow/meta/registry.json`, `workflow/meta/governance_policy.json`, `workflow/meta/version.json`
- **AI context plane:** `workflow/meta/ai_hints.json`, `workflow/meta/ai_navigation.json`, `workflow/meta/semantic_context.json`

---

## F. Deterministic control plane

- Typed constants define canonical runtime values
- Schema guards enforce anchor and runtime consistency
- Drift tests enforce fail-fast behavior on mismatch
- Integrity chain gates release:
  - `validate-suite`
  - `visualize-all`
  - `sync-all`
  - `ai-export`
  - unit tests

---

## G. Temporal and governance coupling

- **Weekly cycle:** Health and incremental improvement
- **Monthly cycle:** Scorecard plus governed apply
- **Quarterly cycle:** Architecture-level cross-feature planning
- **Annual cycle:** Roadmap, drift forecast, ontology and lineage restructuring

**Temporal interpretation:**

- Past, present_past -> QC analysis and semantic health
- Present_future, future -> QA execution, apply mode, release

---

## H. End-to-end lifecycle

1. **Intake**
   - Feature intent enters with MLAS and BTIF semantics.

2. **Build**
   - Artifacts are generated and synchronized deterministically.

3. **Interpret**
   - Semantic intelligence computes drift, inference, conflicts, confidence.

4. **Govern**
   - Approval gates authorize or block apply-mode changes.

5. **Transform**
   - Evolution, expansion, refactor, improvement execute under policy.

6. **Release and regenerate**
   - Release pipeline runs, notes emitted, AI context regenerated.

---

## I. Non-drift rules

- Canonical-first: anchors and metadata are source of truth
- Command-first mutation inside workflow domain
- No unsafe semantic resolve unless explicitly approved
- No release without passing integrity chain

---

## J. Immediate integration work package

1. Add this document to `workflow/meta/docs` and link it from `workflow/README.md`.
2. Bind BaseTrue Studio/Enterprise runtime selectors directly to workflow profiles (weekly/monthly/quarterly/annual).
3. Add cross-system drift tests:
   - BaseTrue anchor <-> workflow registry alignment
   - governance policy <-> apply flag consistency
   - AI context freshness after `release` + `ai-export`.
