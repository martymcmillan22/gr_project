# MLAS + BTIF Canonical Specification

## Canonical Identity Engine (Updated)
This specification now uses the deterministic Basetrue identity model below as the authoritative structure for reasoning, generation, validation, and governance.

### 1. SRL Table (12-Compartment Grid)
- SRL compartments 1-12 map to MLAS + GLCT + HGAE only.
- Phase 1 (MLAS): Math, Language, Arts, Science.
- Phase 2 (GLCT): General Information, Literature, Crafts, Technology.
- Phase 3 (HGAE): History, Geography, Architecture, Ecology.
- Phase 4 subjects are enterprise-only meta governors and do not replace SRL compartments 1-12.

### 2. Phase-to-Sector Map (4x4 = 16 Subjects)
- 16 subjects align to 16 industry groups, 4 sectors, 64 industries, and 256 sub-industries.
- Phase 1 -> Primary sector.
- Phase 2 -> Secondary sector.
- Phase 3 -> Tertiary sector.
- Phase 4 -> Quaternary sector.

### 3. Full 4-Phase Identity Engine
- Phase 1 (Idea): MLAS -> Red, Blue, Yellow, Green.
- Phase 2 (Seed): GLCT -> Purple, Teal, Orange, Lime.
- Phase 3 (Project): HGAE -> Pink, Cyan, Amber, Green-Lime.
- Phase 4 (Meta): Philosophy, Law and Governance, Economics, Systemics -> Deep Crimson, Deep Indigo, Gold-Ochre, Deep Forest.

### 4. Deterministic Rule
- Novice and Intermediate tiers operate on SRL 1-12.
- Advanced and Enterprise tiers extend with Phase 4 quaternary governors.

## Purpose
This document is the canonical, consolidated specification for the captured MLAS and BTIF rules.

It defines:
- Metadata model
- UI routing engine
- Phase, color, metaphor, and category semantics
- Component-pack routing
- Dewey and industry routing
- Semantic presets

## Core Principle
UI routing is determined by this canonical chain:

phase -> mlas -> color -> dewey -> industry -> metaphor -> category -> layout_archetype -> component_pack

Resolver rule: color is derived from phase + MLAS context.

Final UI engine function:

UI = f(phase, mlas, color, dewey, industry, metaphor, category)

## Metadata Envelope
Minimum MDX metadata shape:

```yaml
title: "Slide Title"
mlas:
  subject: math
  branch: sacp
  term: cnic
  meta: ddnc

phase: post
metaphor: mycelium
color:
  primary: purple

dewey:
  code: 500

industry:
  super_sector: financials
  sector: banking
  group: financial-analytics
  sub_industry: quant-finance

ui:
  category: customer
```

Interpretation example from captured source:
"Show a customer-facing, statistics-heavy, financial-analytics view in the Post phase, using purple mycelium semantics."

## MLAS Hierarchy
- Subject layer: 4
- Branch layer: 16
- Term layer: 64
- Meta-term layer: 256

Each deeper layer increases structural precision and controls progressively more specific UI behavior.

## Phase -> Metaphor -> UI Category
| Phase | Metaphor | UI Category |
| --- | --- | --- |
| Create | Immune System | Operations |
| Post | Mycelium | Customer |
| Work | Botanist | Delivery / Executive |

## Color -> Layout Archetype
### Create colors
- red
- blue
- yellow
- green

Layout archetype: matrix

### Post colors
- purple
- teal
- orange
- lime

Layout archetype: journey

### Work colors
- pink
- cyan
- amber
- green-lime

Layout archetype: pipeline

## MLAS Depth -> Component Pack
| MLAS layer | Component family |
| --- | --- |
| Subject (4) | Foundational components |
| Branch (16) | Narrative components |
| Term (64) | Structural components |
| Meta-term (256) | Deep components |

Examples:
- Foundational: tables, matrices, definitions, primitives
- Narrative: storyboards, popovers, tooltips, sequences
- Structural: forms, schemas, grids, workflows
- Deep: semantic inspectors, rule engines, multi-layer views

## Dewey -> Navigation Group
| Dewey range | Navigation group |
| --- | --- |
| 100-400 | Foundations |
| 500-800 | Information |
| 900-1000 | Systems |

## Industry -> Page Signature
| Industry family | Signature |
| --- | --- |
| Financials | Analytical signature |
| Communications | Narrative signature |
| Consumer | Experiential signature |
| Industrials | Operational signature |

## Metaphor -> Behavioral Rules
### Immune System (Create)
- Detect missing metadata
- Highlight anomalies
- Show structural relationships

### Mycelium (Post)
- Branch content
- Replicate patterns
- Show lineage

### Botanist (Work)
- Show evolution
- Show dependencies
- Show constraints

## Semantic Presets
Preset definition:

preset = phase + color + mlas + dewey + industry + metaphor + ui_category

Applying a preset auto-fills:
- phase
- color
- mlas subject/branch/term/meta
- dewey code
- industry mapping
- metaphor
- ui category
- layout archetype
- component pack

### Preset Families
1. Create presets -> Immune System -> Operations
2. Post presets -> Mycelium -> Customer
3. Work presets -> Botanist -> Delivery/Executive

Each family has four presets, aligned to the 12-color system.

## Canonical Preset Catalog
### Create family
1. create.red.math
   - MLAS: math
   - Dewey: 100
   - Color: red
   - Metaphor: immune system (red cells)
   - UI: operations
   - Industry: financials
2. create.blue.language
   - MLAS: language
   - Dewey: 200
   - Color: blue
   - Metaphor: immune system (blue cells)
   - UI: operations
   - Industry: communications
3. create.yellow.arts
   - MLAS: arts
   - Dewey: 300
   - Color: yellow
   - Metaphor: immune system (plasma)
   - UI: operations
   - Industry: consumer
4. create.green.science
   - MLAS: science
   - Dewey: 400
   - Color: green
   - Metaphor: immune system (platelets)
   - UI: operations
   - Industry: industrials

### Post family
1. post.purple.statistics
   - MLAS: sacp
   - Dewey: 500
   - Color: purple
   - Metaphor: mycelium (spores)
   - UI: customer
   - Industry: information
2. post.teal.literature
   - MLAS: ednp
   - Dewey: 600
   - Color: teal
   - Metaphor: mycelium (hypha)
   - UI: customer
   - Industry: publishing
3. post.orange.crafts
   - MLAS: vlsm
   - Dewey: 700
   - Color: orange
   - Metaphor: mycelium (pinhead)
   - UI: customer
   - Industry: arts-and-recreation
4. post.lime.technology
   - MLAS: mbsp
   - Dewey: 800
   - Color: lime
   - Metaphor: mycelium (fruit)
   - UI: customer
   - Industry: technology

### Work family
1. work.pink.history
   - MLAS: history
   - Dewey: 900
   - Color: pink
   - Metaphor: botanist (structure)
   - UI: delivery
   - Industry: systems
2. work.cyan.geography
   - MLAS: geography
   - Dewey: 1000
   - Color: cyan
   - Metaphor: botanist (function)
   - UI: delivery
   - Industry: logistics
3. work.amber.industry
   - MLAS: industry
   - Dewey: 900-1000
   - Color: amber
   - Metaphor: botanist (genetics)
   - UI: executive
   - Industry: enterprise
4. work.greenlime.systems
   - MLAS: systems
   - Dewey: 900-1000
   - Color: green-lime
   - Metaphor: botanist (evolution)
   - UI: executive
   - Industry: infrastructure

## Preset Runtime Example
Input preset:

```yaml
preset: post.purple.statistics
```

Inherited metadata:

```yaml
phase: post
color: purple
mlas.branch: sacp
dewey.code: 500
metaphor: mycelium
ui.category: customer
industry.sector: information
layout: journey
components: narrative-pack
```

## Contract Notes
- This spec is semantic-first; UI assembly must be deterministic from metadata.
- No manual UI wiring should be needed when metadata is complete.
- Missing metadata should trigger behavior from metaphor-driven rule checks.
