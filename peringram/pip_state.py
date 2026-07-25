"""
Unified PIP (Peringram) context and workflow-gating layer.

`PIPState` is a lightweight, read-only snapshot of a user's current Recycle3
allocation, derived sector tier, and lifecycle stage. It is attached to view
context as `pip_state` (e.g. `pip_state.recycle3`, `pip_state.sector_tier`).

Later phases will extend `PIPState` with additional attributes:
- Phase 2 (SRL Maps): `pip_state.territory`
- Phase 4 (Convection-Cycle): `pip_state.time_slot`

`PIPWorkflowService` gates PIP lifecycle actions (Idea -> Seed -> Project ->
Enterprise) based on the user's current sector tier.
"""

from .models import LIFECYCLE_ORDER, TIER_TO_LIFECYCLE, PIPLifecycle


class PIPState:
    """Unified, read-only PIP context for a single user/request."""

    def __init__(self, recycle3, sector_tier, lifecycle_stage):
        self.recycle3 = recycle3
        self.sector_tier = sector_tier
        self.lifecycle_stage = lifecycle_stage

        # RR (Repository Relay) unlocks at Project tier (CCPP); QPU unlocks at
        # Enterprise tier (DCHD). Deeper integration with the workflow/ Strict
        # Mode QPU engine itself is out of scope for Phase 1 (see repo memory
        # note repository-relay-component.md and PIP phase notes).
        self.rr_unlocked = LIFECYCLE_ORDER.index(lifecycle_stage) >= LIFECYCLE_ORDER.index(PIPLifecycle.PROJECT)
        self.qpu_unlocked = lifecycle_stage == PIPLifecycle.ENTERPRISE

    @classmethod
    def from_recycle3(cls, recycle3_profile):
        sector_tier = recycle3_profile.calculate_sector_tier()
        lifecycle_stage = TIER_TO_LIFECYCLE[sector_tier]
        return cls(recycle3=recycle3_profile, sector_tier=sector_tier, lifecycle_stage=lifecycle_stage)


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
