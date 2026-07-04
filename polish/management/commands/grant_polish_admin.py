from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from polish.views import POLISH_ADMIN_GROUP_NAME


class Command(BaseCommand):
    help = "Grant or revoke polish_admin group membership without changing Django staff access."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            action="append",
            default=[],
            help="User email to grant/revoke polish_admin role (repeat for multiple users).",
        )
        parser.add_argument(
            "--username",
            action="append",
            default=[],
            help="Username to grant/revoke polish_admin role (repeat for multiple users).",
        )
        parser.add_argument(
            "--revoke",
            action="store_true",
            help="Remove polish_admin role instead of granting it.",
        )

    def handle(self, *args, **options):
        emails = [value.strip() for value in (options.get("email") or []) if value and value.strip()]
        usernames = [value.strip() for value in (options.get("username") or []) if value and value.strip()]
        revoke = bool(options.get("revoke"))

        if not emails and not usernames:
            raise CommandError("Provide at least one --email or --username value.")

        User = get_user_model()
        selector = Q()
        if emails:
            selector |= Q(email__in=emails)
        if usernames:
            selector |= Q(username__in=usernames)

        users = list(User.objects.filter(selector).distinct())
        if not users:
            raise CommandError("No users matched the provided selectors.")

        group, _ = Group.objects.get_or_create(name=POLISH_ADMIN_GROUP_NAME)

        changed = 0
        unchanged = 0
        action_verb = "revoked" if revoke else "granted"

        for user in users:
            has_role = user.groups.filter(name=group.name).exists()
            if revoke:
                if has_role:
                    user.groups.remove(group)
                    changed += 1
                    self.stdout.write(self.style.SUCCESS(f"Polish admin revoked for {user.email or user.username}."))
                else:
                    unchanged += 1
                    self.stdout.write(f"No change for {user.email or user.username}: role not assigned.")
            else:
                if has_role:
                    unchanged += 1
                    self.stdout.write(f"No change for {user.email or user.username}: role already assigned.")
                else:
                    user.groups.add(group)
                    changed += 1
                    self.stdout.write(self.style.SUCCESS(f"Polish admin granted for {user.email or user.username}."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed: {action_verb}={changed}, unchanged={unchanged}, target_group={group.name}."
            )
        )
