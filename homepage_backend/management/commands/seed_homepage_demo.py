from django.core.management.base import BaseCommand

from homepage_backend.models import HomepageAction, HomepageFlow, HomepagePreference, HomepageTask
from users.models import User


class Command(BaseCommand):
    help = "Create or reset repeatable homepage demo data for a single user."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="homepage.demo@grassroots.local")
        parser.add_argument("--username", default="homepage_demo")
        parser.add_argument("--name", default="Homepage Demo User")
        parser.add_argument("--password", default="DemoPass123!")

    def handle(self, *args, **options):
        email = options["email"]
        username = options["username"]
        name = options["name"]
        password = options["password"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "name": name},
        )

        if not created:
            user.username = username
            user.name = name

        user.set_password(password)
        user.save(update_fields=["username", "name", "password"])

        # Reset user-scoped homepage data so every run is deterministic.
        HomepageTask.objects.filter(owner=user).delete()
        HomepageFlow.objects.filter(owner=user).delete()
        HomepageAction.objects.filter(owner=user).delete()
        HomepagePreference.objects.filter(owner=user).delete()

        flow = HomepageFlow.objects.create(
            owner=user,
            name="Daily Launch Flow",
            status=HomepageFlow.STATUS_ACTIVE,
            progress=42,
            message="In progress",
        )

        tasks = [
            HomepageTask.objects.create(
                owner=user,
                title="Review Notes",
                description="Check today's flow",
                status=HomepageTask.STATUS_TODO,
            ),
            HomepageTask.objects.create(
                owner=user,
                title="Update Settings",
                description="Adjust preferences",
                status=HomepageTask.STATUS_DOING,
            ),
        ]

        preference = HomepagePreference.objects.create(
            owner=user,
            notifications=True,
            dark_mode=False,
        )

        actions = [
            HomepageAction.objects.create(owner=user, label="Start Flow", metadata={"source": "seed"}),
            HomepageAction.objects.create(owner=user, label="Open Taskboard", metadata={"source": "seed"}),
        ]

        self.stdout.write(self.style.SUCCESS("Homepage demo seed complete."))
        self.stdout.write(f"user_email={user.email}")
        self.stdout.write(f"password={password}")
        self.stdout.write(f"flow_id={flow.id}")
        self.stdout.write(f"task_ids={[task.id for task in tasks]}")
        self.stdout.write(f"preference_id={preference.id}")
        self.stdout.write(f"action_ids={[action.id for action in actions]}")
