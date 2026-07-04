from django.utils import timezone

from .models import PolishReminderPreference, PolishTask


def get_daily_polish_reminder(user, source_label="Twist"):
    if not user.is_authenticated:
        return {"show_popup": False, "message": "", "count": 0}

    preference, _ = PolishReminderPreference.objects.get_or_create(user=user)
    incomplete_count = PolishTask.objects.filter(user=user, is_completed=False).count()

    if not preference.enabled or incomplete_count == 0:
        return {"show_popup": False, "message": "", "count": incomplete_count}

    today = timezone.localdate()
    if preference.last_reminded_on == today:
        return {"show_popup": False, "message": "", "count": incomplete_count}

    preference.last_reminded_on = today
    preference.save(update_fields=["last_reminded_on"])

    message = (
        f"Polish reminder from {source_label}: "
        f"you have {incomplete_count} unfinished task"
        f"{'s' if incomplete_count != 1 else ''}."
    )
    return {
        "show_popup": True,
        "message": message,
        "count": incomplete_count,
    }
