from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from peringram.pip_state import IDEA_TO_SEED_ALLOWED_TIME_FRAMES
from peringram.srl import SRLService

from .models import Idea
from .services import RawToSeedPolishService


@receiver(pre_save, sender=Idea)
def idea_transition_precheck(sender, instance, **kwargs):
    previous_status = None
    if instance.pk:
        previous_status = sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()

    instance._previous_status = previous_status

    should_validate = (
        (previous_status == Idea.STATUS_RAW and instance.status == Idea.STATUS_SEED)
        or (previous_status is None and instance.status == Idea.STATUS_SEED)
    )
    if should_validate:
        RawToSeedPolishService(instance).validate_transition()

        # Phase 4 (PIP): RAW -> SEED is only allowed in "analysis/planning"
        # Convection-Cycle slots (present_past/present_future).
        current_slot = SRLService.current_convection_compartment()
        current_time_frame = SRLService.convection_time_frame(current_slot)
        if current_time_frame not in IDEA_TO_SEED_ALLOWED_TIME_FRAMES:
            raise ValidationError(
                {
                    "status": (
                        "RAW -> SEED is only allowed during present_past/present_future "
                        f"Convection slots; current time_frame={current_time_frame}."
                    )
                }
            )


@receiver(post_save, sender=Idea)
def create_seed_on_raw_to_seed(sender, instance, created, **kwargs):
    previous_status = getattr(instance, "_previous_status", None)
    should_run = (
        (previous_status == Idea.STATUS_RAW and instance.status == Idea.STATUS_SEED)
        or (created and instance.status == Idea.STATUS_SEED)
    )
    if should_run:
        RawToSeedPolishService(instance).run()