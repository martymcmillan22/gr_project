"""
Unified PIP (Peringram) context and workflow-gating layer.

`PIPState` is a lightweight, read-only snapshot of a user's current Recycle3
allocation, SRL territory, derived sector tier, and lifecycle stage. It is
attached to view context as `pip_state` (e.g. `pip_state.recycle3`,
`pip_state.sector_tier`, `pip_state.territory`).

Later phases will extend `PIPState` further:
- Phase 4 (Convection-Cycle): richer temporal automation hooks

`PIPWorkflowService` gates PIP lifecycle actions (Idea -> Seed -> Project ->
Enterprise) based on the user's current sector tier.
"""

"""
Unified PIP (Peringram) context and workflow-gating layer.

`PIPState` is a lightweight, read-only snapshot of a user's current Recycle3
allocation, SRL territory, sector-group tier, combined final tier, and
lifecycle stage. It is attached to view context as `pip_state` (e.g.
`pip_state.recycle3`, `pip_state.final_tier`, `pip_state.territory`).

Tier signals (Phase 1-3):
- `sector_tier`: Recycle3 + SRL boost only (Phase 1/2, unchanged for
  backward compatibility).
- `sector_group_tier`: derived from the user's SRL-mapped IndustryGroup
  (Phase 3), boosted by the same SRL time_frame boost.
- `final_tier`: max(recycle3-only tier, boosted sector_group_tier), capped at
  DCHD. This is now the AUTHORITATIVE tier for `lifecycle_stage`,
  `rr_unlocked`, `qpu_unlocked`, and bureau access.

`PIPWorkflowService` gates PIP lifecycle actions (Idea -> Seed -> Project ->
Enterprise) and bureau access (BOS/BOL/BOE/BOP) based on `final_tier`.
"""

from .models import (
    LIFECYCLE_ORDER,
    TIER_ORDER,
    TIER_TO_LIFECYCLE,
    IndustryGroup,
    PIPLifecycle,
    SectorTier,
    industry_group_code_for_lattice_index,
)
from .srl import SRLService

# Bureau -> minimum required tier (BOS/BOL/BOE/BOP correspond to SRL indices
# 1-4 / IndustryGroup codes 1-4, i.e. Sector A, per the Phase 3 checklist).
BUREAU_TIER_REQUIREMENTS = {
    "bos": SectorTier.MLAS,
    "bol": SectorTier.SEVM,
    "boe": SectorTier.CCPP,
    "bop": SectorTier.DCHD,
}


class PIPState:
    """Unified, read-only PIP context for a single user/request."""

    def __init__(self, recycle3, sector_tier, lifecycle_stage, territory=None, srl_tier_boost=None):
        self.recycle3 = recycle3
        self.sector_tier = sector_tier
        self.territory = territory
        self.srl_tier_boost = srl_tier_boost if srl_tier_boost is not None else 0

        if territory is not None:
            self.industry_group_code = industry_group_code_for_lattice_index(territory.index)
        else:
            self.industry_group_code = None

        # Section 1-2: sector_group_tier, from the user's SRL-mapped IndustryGroup
        # (reuses the existing UserLatticeAssignment/territory - no separate
        # per-user IndustryGroup assignment model is introduced).
        group = None
        if self.industry_group_code is not None:
            group = IndustryGroup.objects.filter(code=self.industry_group_code).first()
        self.sector_group = group
        base_sector_group_tier = group.sector_tier if group is not None else SectorTier.MLAS

        group_index = TIER_ORDER.index(base_sector_group_tier)
        boost = self.srl_tier_boost
        boosted_group_index = group_index + (1 if boost >= 0.5 else 0)
        boosted_group_index = min(boosted_group_index, len(TIER_ORDER) - 1)
        self.sector_group_tier = TIER_ORDER[boosted_group_index]

        # Section 3: final_tier = max(recycle3-only tier, boosted sector_group_tier).
        recycle3_only_tier = recycle3.calculate_sector_tier() if recycle3 is not None else SectorTier.MLAS
        recycle3_index = TIER_ORDER.index(recycle3_only_tier)
        final_index = max(recycle3_index, boosted_group_index)
        self.final_tier = TIER_ORDER[final_index]

        self.lifecycle_stage = TIER_TO_LIFECYCLE[self.final_tier]

        # RR (Repository Relay) unlocks at Project tier (CCPP); QPU unlocks at
        # Enterprise tier (DCHD). Deeper integration with the workflow/ Strict
        # Mode QPU engine's node internals remains out of scope (see repo
        # memory note repository-relay-component.md and PIP phase notes) -
        # QPUService (Phase 3) only wraps payload prep + a tier gate, it does
        # not modify the Strict Mode engine itself.
        self.rr_unlocked = LIFECYCLE_ORDER.index(self.lifecycle_stage) >= LIFECYCLE_ORDER.index(PIPLifecycle.PROJECT)
        self.qpu_unlocked = self.lifecycle_stage == PIPLifecycle.ENTERPRISE

        # Section 4: bureau access, keyed by slug (bos/bol/boe/bop).
        self.bureau_access = {
            bureau: final_index >= TIER_ORDER.index(required_tier)
            for bureau, required_tier in BUREAU_TIER_REQUIREMENTS.items()
        }

        # SRL <-> Convection-Cycle mapping (Section 5): the currently active
        # world-clock slot, and what it unlocks.
        self.time_slot = SRLService.current_convection_compartment()
        self.time_slot_time_frame = SRLService.convection_time_frame(self.time_slot)
        self.enterprise_planning_unlocked = self.time_slot_time_frame == "future"
        self.archival_analysis_unlocked = self.time_slot_time_frame == "past"

    @classmethod
    def from_recycle3(cls, recycle3_profile, territory=None):
        sector_tier = recycle3_profile.calculate_sector_tier(territory)
        srl_tier_boost = recycle3_profile.calculate_srl_boost(territory)
        return cls(
            recycle3=recycle3_profile,
            sector_tier=sector_tier,
            lifecycle_stage=None,  # computed internally from final_tier
            territory=territory,
            srl_tier_boost=srl_tier_boost,
        )


class PIPWorkflowService:
    """Gates PIP lifecycle actions (Idea/Seed/Project/Enterprise) based on sector tier."""

    @staticmethod
    def max_allowed_stage(sector_tier):
        return TIER_TO_LIFECYCLE[sector_tier]

    @staticmethod
    def can_perform_action(action, pip_state):
        """Return True if `action` (a PIPLifecycle value) is allowed under pip_state's current tier."""
        return LIFECYCLE_ORDER.index(action) <= LIFECYCLE_ORDER.index(pip_state.lifecycle_stage)

    @staticmethod
    def allowed_stages(pip_state):
        """Return the list of PIPLifecycle stages currently allowed for this pip_state."""
        max_index = LIFECYCLE_ORDER.index(pip_state.lifecycle_stage)
        return LIFECYCLE_ORDER[: max_index + 1]

    @staticmethod
    def can_access_bureau(bureau_code, pip_state):
        """Return True if pip_state's final_tier meets the bureau's minimum tier requirement."""
        required_tier = BUREAU_TIER_REQUIREMENTS.get(bureau_code.lower())
        if required_tier is None:
            return True  # not a gated bureau
        return TIER_ORDER.index(pip_state.final_tier) >= TIER_ORDER.index(required_tier)
