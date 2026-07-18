BaseTrue Memory Anchor Instructions (for VS Code AI)

1. Always load /basetrue/anchors/bt_anchor.json before generating or editing components.
2. Do NOT redefine:
   - BTIF (BaseTrue Information Format)
   - BTPE (BaseTrue Phase Engine)
   - Temporal Grid
   - Geometry Modes
   - Tier Ladder
   - QPU Growth Model
3. Use logic helpers in /basetrue/logic:
   - temporalRouting.ts for temporal behavior
   - tierLogic.ts for tier behavior
   - geometryMode.ts for geometry behavior
   - qpuGrowth.ts for QPU counts
4. Compartment pages are READ-ONLY lenses over artifacts from:
   - Corporation (Create)
   - Museum (Post)
   - Garden (Work)
5. Tiers:
   - Novice: 4 commands, no RR, no QPU
   - Intermediate: 4 + 16 commands, RR only
   - Advanced: 4 + 16 + 64 commands, RR only
   - Studio: 4 + 16 + 64 commands, RR + scaled QPU (up to compartment 8), 50 GB storage
   - Enterprise: full RR + full QPU tower (up to compartment 12)
6. Geometry:
   - RR = circle
   - QPU = square
   - Tower = vertical stack
   - Modes: architectural -> layered -> flat
   - Transitions: animated on large screens, instant on small screens

7. Canonical Novice + Intermediate Blueprint (locked):
    - Tier identities:
       - Corporation -> Architect
       - Museum -> Full-Stack Engineer
       - Garden -> Botanist
    - Tier logic:
       - Novice = MLAS (4-step)
       - Intermediate = SVEM (16-step)
    - Compartment behavior:
       - Compartments are read-only lenses.
       - Editing occurs only in pipeline mode and Studio/Enterprise workspaces.
    - Museum structure (corrected canonical model):
       - Wings: Duseum (descriptive), Nuseum (narrative), Library (read-only), Monuments (presentation + checkout)
       - DATA resides in Duseum -> Library flank
       - LOGIC resides in Duseum
       - JAVA resides in Nuseum
       - TEMPLATES resides in Nuseum -> Monuments
    - Temporal ownership:
       - QC (user): past + present_past
       - QA (VA): present_future + future
    - Power-of-4 color quadrants:
       - Corporation: red, blue, yellow, green
       - Museum: purple, teal, orange, lime
       - Garden: pink, cyan, amber, green_lime
    - Museum 16-step sections (SVEM):
       - DATA: Select/Form/Hierarchical; Action/Table/Network; Query/Parameter/Object; Cross/Report/Relational
       - LOGIC: Data; Program; Which; Template
       - JAVA: Keyword; Operator; Expression; Value
       - TEMPLATES: Chest/Forms/Widgets; Info/Retrieve/Process; Assist/Step-by-Step; Checkout/Survey/Polls

8. Determinism and continuity:
    - RR routing drives QPU planning.
    - QPU planning drives floor and work orchestration.
    - Tagging is deterministic and uses shared ArtifactTagDisplay.
    - Studio uses scaled QPU only.
    - Enterprise is the full tower control room.

9. Canonical Studio + Enterprise Blueprint (locked):
    - Studio identity:
       - Semantic workstation.
       - Inherits Museum 16-step model as 16 semantic blocks.
       - No tower floors, scaled QPU only, semantic overlays only.
    - Enterprise identity:
       - Semantic skyscraper.
       - Inherits Museum 16-step model as 16 tower floors.
       - Full QPU, multi-floor orchestration, timeline and floor navigation.
    - Shared section semantics (4x4 = 16):
       - DATA (Duseum -> Library): safe modification layer, Library read-only.
       - LOGIC (Duseum): descriptive flow and rules.
       - JAVA (Nuseum): narrative action and execution.
       - TEMPLATES (Nuseum -> Monuments): narrative presentation and delivery.
    - Guided chain:
       - Monuments -> Checkout -> Surveys -> Polls.
    - Temporal ownership:
       - QC (user): past + present_past.
       - QA (VA): present_future + future.
    - Enterprise tower zoning (4 zones x 4 floors = 16):
       - Zone 1 DATA: 4 lower floors.
       - Zone 2 LOGIC: 4 lower floors.
       - Zone 3 JAVA: 4 upper floors.
       - Zone 4 TEMPLATES: 4 upper floors.
    - Garden maintenance execution layer:
       - manufacturing
       - contractors
       - logistics
       - shipping
