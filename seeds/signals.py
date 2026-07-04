from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

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


@receiver(post_save, sender=Idea)
def create_seed_on_raw_to_seed(sender, instance, created, **kwargs):
    previous_status = getattr(instance, "_previous_status", None)
    should_run = (
        (previous_status == Idea.STATUS_RAW and instance.status == Idea.STATUS_SEED)
        or (created and instance.status == Idea.STATUS_SEED)
    )
    if should_run:
        RawToSeedPolishService(instance).run()