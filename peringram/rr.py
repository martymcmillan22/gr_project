"""
RR (Repository Relay) service for PIP - the "yellow tier engine".

RR did not previously exist as backend code (confirmed during Phase 3
investigation - only the Penpot design artifact existed). This module handles
the Seed -> Project (seeds.Business) promotion, gated at CCPP tier, reusing
the existing SRL validation from Phase 2 (PIPSRLValidator) rather than
duplicating capacity/time_frame/tag logic.

NOTE: `seeds` already imports from `peringram.models`, so `peringram` must
never import from `seeds` at module load time (circular import). All
references to `seeds` below are local/deferred imports inside function bodies.

Scope note: "tagging" and "temporal routing" (mentioned in the Phase 3
checklist) are satisfied via the existing PIPSRLValidator tag-requirement
checks and pip_state.time_slot_time_frame exposure, respectively - no new
tag/temporal model or restriction is introduced here, since none was
concretely specified beyond what Phase 2 already built.

Project -> Enterprise promotion is explicitly deferred to Phase 4 (Enterprise
does not exist as a seeds lifecycle state yet).
"""

from .srl import PIPSRLValidator


class RRAccessDeniedError(Exception):
    """Raised when an RR action is attempted below the required tier."""


class RRService:
    """Gates and performs Seed -> Project (RR) promotions."""

    @staticmethod
    def can_invoke(pip_state):
        """RR unlocks at CCPP tier or higher (see pip_state.rr_unlocked)."""
        return pip_state.rr_unlocked

    @staticmethod
    def promote_seed_to_project(pip_state, seed, brand_name, market_status="draft", metadata=None):
        """
        Promote a seeds.Seed to a seeds.Business ("Project"), gated at CCPP tier
        and validated against the user's SRL compartment (capacity/time_frame/tags).
        """
        from seeds.models import Business  # deferred: avoid circular import

        if not RRService.can_invoke(pip_state):
            raise RRAccessDeniedError(
                f"RR requires CCPP tier or higher; current tier is {pip_state.final_tier}."
            )

        if pip_state.territory is not None:
            validation = PIPSRLValidator.validate(
                compartment_id=pip_state.territory.index,
                raw_content=seed.idea.raw_content,
                metadata=metadata,
            )
            if validation["status"] != "approved":
                raise RRAccessDeniedError(f"SRL validation failed: {validation.get('reason')}")

        business, _ = Business.objects.update_or_create(
            seed=seed,
            defaults={"brand_name": brand_name, "market_status": market_status},
        )
        seed.idea.status = "PROJECT"
        seed.idea.save(update_fields=["status", "updated_at"])
        return business

    @staticmethod
    def promote_project_to_enterprise(pip_state, business):
        """Project -> Enterprise promotion. Deferred to Phase 4 (ENTERPRISE state doesn't exist yet)."""
        raise NotImplementedError("Project -> Enterprise promotion is implemented in Phase 4.")
