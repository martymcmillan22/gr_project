"""
SRL (Square Root Lattice) territorial/temporal integration for PIP.

- `SRLService` assigns each user a deterministic lattice compartment (territory),
  and derives the "current" ConvectionCompartment / its effective time_frame.
- `PIPSRLValidator` wraps (does NOT rewrite) the existing seeds app's
  `validate_idea_submission()`, exposing granular capacity/time_frame booleans
  for the PIP dashboard.

NOTE: `seeds` already imports from `peringram.models`, so `peringram` must never
import from `seeds` at module load time (circular import). All references to
`seeds` below are local/deferred imports inside function bodies.
"""

from django.utils import timezone

from .models import ConvectionCompartment, LatticeCompartment, UserLatticeAssignment


class SRLService:
    """Assigns and resolves a user's SRL (Square Root Lattice) territory."""

    @staticmethod
    def assign_compartment(user):
        """
        Deterministically assign a user to one of the 12 lattice compartments.

        ASSUMPTION (not specified in the Phase 2 checklist): compartment index is
        derived from `((user.id - 1) % 12) + 1`, spreading users evenly and
        reproducibly across the 12 compartments. Flag if a different rule
        (e.g. user choice, Recycle3-derived) is intended instead.
        """
        assignment = UserLatticeAssignment.objects.filter(user=user).select_related("lattice_compartment").first()
        if assignment is not None:
            return assignment.lattice_compartment

        index = ((user.id - 1) % 12) + 1
        compartment = LatticeCompartment.objects.get(index=index)
        UserLatticeAssignment.objects.create(user=user, lattice_compartment=compartment)
        return compartment

    @staticmethod
    def lattice_index_for_convection(convection_compartment):
        """Map a 24-slot ConvectionCompartment onto its corresponding 1-12 lattice index."""
        return ((convection_compartment.compartment_index - 1) % 12) + 1

    @staticmethod
    def current_convection_compartment():
        """The ConvectionCompartment matching the current UTC hour (world clock)."""
        current_hour = timezone.now().hour
        return ConvectionCompartment.objects.filter(world_clock_hour=current_hour).first()

    @staticmethod
    def convection_time_frame(convection_compartment):
        """Derive the effective time_frame of a ConvectionCompartment via its mapped lattice compartment."""
        if convection_compartment is None:
            return None
        lattice_index = SRLService.lattice_index_for_convection(convection_compartment)
        compartment = LatticeCompartment.objects.filter(index=lattice_index).first()
        return compartment.time_frame if compartment else None


class PIPSRLValidator:
    """
    Wraps the existing `seeds.services.validate_idea_submission()` (unmodified)
    and exposes granular pass/fail booleans for PIP dashboard display.
    """

    @staticmethod
    def validate(compartment_id, raw_content, metadata=None):
        from seeds.services import validate_idea_submission  # deferred: avoid circular import

        metadata = metadata or {}
        result = validate_idea_submission(compartment_id, raw_content, metadata)

        compartment = LatticeCompartment.objects.filter(index=compartment_id).first()
        content_length = len((raw_content or "").strip())
        capacity_ok = compartment is not None and content_length <= compartment.capacity

        tags = set(metadata.get("tags", []))
        time_frame_ok = True
        if compartment is not None:
            if compartment.time_frame == LatticeCompartment.TIME_PAST and "historical" not in tags:
                time_frame_ok = False
            if compartment.time_frame == LatticeCompartment.TIME_FUTURE and "forecast" not in tags:
                time_frame_ok = False

        return {
            "status": result.get("status"),
            "reason": result.get("reason"),
            "capacity_ok": capacity_ok,
            "time_frame_ok": time_frame_ok,
            "tag_requirements_ok": time_frame_ok,
        }
