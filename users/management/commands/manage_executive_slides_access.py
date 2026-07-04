from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError


GROUP_NAME = "executive_slides_access"


class Command(BaseCommand):
    help = "Grant or revoke executive slides access for users by email or for all staff users."

    def add_arguments(self, parser):
        action_group = parser.add_mutually_exclusive_group(required=True)
        action_group.add_argument("--grant", action="store_true", help="Grant access.")
        action_group.add_argument("--revoke", action="store_true", help="Revoke access.")

        parser.add_argument(
            "--emails",
            nargs="+",
            help="Email addresses to target (space separated).",
        )
        parser.add_argument(
            "--all-staff",
            action="store_true",
            help="Apply to all users with is_staff=True.",
        )

    def handle(self, *args, **options):
        emails = options.get("emails") or []
        all_staff = options.get("all_staff")
        grant = options.get("grant")

        if not emails and not all_staff:
            raise CommandError("Provide --emails or --all-staff.")

        User = get_user_model()
        queryset = User.objects.filter(is_staff=True) if all_staff else User.objects.filter(email__in=emails)
        total = queryset.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No matching users found."))
            return

        group, _ = Group.objects.get_or_create(name=GROUP_NAME)

        if grant:
            for user in queryset:
                user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f"Granted access for {total} user(s)."))
            return

        for user in queryset:
            user.groups.remove(group)
        self.stdout.write(self.style.SUCCESS(f"Revoked access for {total} user(s)."))
