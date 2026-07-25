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

from .models import (
    LIFECYCLE_ORDER,
    TIER_TO_LIFECYCLE,
    PIPLifecycle,
    industry_group_code_for_lattice_index,
)
from .srl import SRLService


class PIPState:
    """Unified, read-only PIP context for a single user/request."""

    def __init__(self, recycle3, sector_tier, lifecycle_stage, territory=None, srl_tier_boost=None):
        self.recycle3 = recycle3
        self.sector_tier = sector_tier
        self.lifecycle_stage = lifecycle_stage
        self.territory = territory
        self.srl_tier_boost = srl_tier_boost

        # RR (Repository Relay) unlocks at Project tier (CCPP); QPU unlocks at
        # Enterprise tier (DCHD). Deeper integration with the workflow/ Strict
        # Mode QPU engine itself is out of scope for Phase 1-2 (see repo memory
        # note repository-relay-component.md and PIP phase notes).
        self.rr_unlocked = LIFECYCLE_ORDER.index(lifecycle_stage) >= LIFECYCLE_ORDER.index(PIPLifecycle.PROJECT)
        self.qpu_unlocked = lifecycle_stage == PIPLifecycle.ENTERPRISE

        if territory is not None:
            self.industry_group_code = industry_group_code_for_lattice_index(territory.index)
        else:
            self.industry_group_code = None

        # SRL <-> Convection-Cycle mapping (Section 5): the currently active
        # world-clock slot, and what it unlocks.
        self.time_slot = SRLService.current_convection_compartment()
        self.time_slot_time_frame = SRLService.convection_time_frame(self.time_slot)
        self.enterprise_planning_unlocked = self.time_slot_time_frame == "future"
        self.archival_analysis_unlocked = self.time_slot_time_frame == "past"

    @classmethod
    def from_recycle3(cls, recycle3_profile, territory=None):
        sector_tier = recycle3_profile.calculate_sector_tier(territory)
        lifecycle_stage = TIER_TO_LIFECYCLE[sector_tier]
        srl_tier_boost = recycle3_profile.calculate_srl_boost(territory)
        return cls(
            recycle3=recycle3_profile,
            sector_tier=sector_tier,
            lifecycle_stage=lifecycle_stage,
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
