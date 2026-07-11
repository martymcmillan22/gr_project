import keyword
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from platform_core.presentation_mdx import sync_presentation_blueprints


APP_CONFIG_TEMPLATE = """from django.apps import AppConfig


class {class_name}(AppConfig):
    default_auto_field = \"django.db.models.BigAutoField\"
    name = \"{app_name}\"
"""

MODELS_TEMPLATE = """from django.db import models

from platform_core.backend import BaseModel, OwnedModel


class {model_name}(OwnedModel, BaseModel):
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = [\"-updated_at\"]
        permissions = [
            (\"view_{model_snake}_analytics\", \"Can view {model_name} analytics\"),
        ]

    def __str__(self):
        return self.title
"""

SERIALIZERS_TEMPLATE = """from rest_framework import serializers

from platform_core.backend import BaseSerializer

from .models import {model_name}


class {model_name}Serializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = {model_name}
"""

PERMISSIONS_TEMPLATE = """from platform_core.backend import BasePermissions


class {model_name}Permissions(BasePermissions):
    pass
"""

VIEWS_TEMPLATE = """from platform_core.backend import BaseView

from .models import {model_name}
from .permissions import {model_name}Permissions
from .serializers import {model_name}Serializer


class {model_name}ViewSet(BaseView):
    queryset = {model_name}.objects.all()
    serializer_class = {model_name}Serializer
    permission_classes = BaseView.permission_classes + [{model_name}Permissions]
"""

URLS_TEMPLATE = """from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import {model_name}ViewSet

router = DefaultRouter()
router.register(r\"items\", {model_name}ViewSet, basename=\"{slug}-items\")

urlpatterns = [
    path(\"api/\", include(router.urls)),
]
"""

ADMIN_TEMPLATE = """from django.contrib import admin

from .models import {model_name}


@admin.register({model_name})
class {model_name}Admin(admin.ModelAdmin):
    list_display = (\"id\", \"title\", \"owner\", \"is_active\", \"updated_at\")
    list_filter = (\"is_active\",)
    search_fields = (\"title\", \"summary\", \"owner__username\", \"owner__email\")
"""

TESTS_TEMPLATE = """from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import {model_name}


class {model_name}ApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=\"{slug}-owner\",
            email=\"{slug}@example.com\",
            password=\"testpass123\",
            name=\"{model_name} Owner\",
        )
        self.other = User.objects.create_user(
            username=\"{slug}-other\",
            email=\"{slug}-other@example.com\",
            password=\"testpass123\",
            name=\"{model_name} Other\",
        )
        self.client.force_authenticate(self.user)

    def test_create_assigns_owner(self):
        url = reverse(\"{slug}-items-list\")
        response = self.client.post(url, {{\"title\": \"Sample\", \"summary\": \"Body\"}}, format=\"json\")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = {model_name}.objects.get(id=response.data[\"id\"])
        self.assertEqual(item.owner_id, self.user.id)

    def test_non_owner_cannot_read_item(self):
        item = {model_name}.objects.create(owner=self.user, title=\"A\")
        self.client.force_authenticate(self.other)

        url = reverse(\"{slug}-items-detail\", args=[item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
"""

FRONTEND_ROUTE_TEMPLATE = """import { lazy } from \"react\";

export const __PAGE_NAME__Route = {
    path: \"/__SLUG__\",
    component: lazy(() => import(\"./pages/__PAGE_NAME__Page\")),
};
"""

FRONTEND_PAGE_TEMPLATE = """import {
    DashboardCard,
    FlowPanel,
    QuickActions,
    SettingsPanel,
    Taskboard,
} from "../../../workflow/ui_templates/penpot_templates/index";

export default function __PAGE_NAME__Page() {
    return (
        <div style={{ display: \"grid\", gap: \"1rem\" }}>
            <DashboardCard title="__PAGE_NAME__ Dashboard" description="Generated one-pager shell" />
            <Taskboard
                title="__PAGE_NAME__ Tasks"
                tasks={[
                    { id: \"1\", label: \"Connect API\", status: \"todo\" },
                    { id: \"2\", label: \"Review metrics\", status: \"doing\" },
                ]}
            />
            <FlowPanel
                title=\"Data Flow\"
                nodes={[
                    { id: \"capture\", label: \"Capture\" },
                    { id: \"validate\", label: \"Validate\" },
                    { id: \"publish\", label: \"Publish\" },
                ]}
            />
            <QuickActions
                actions={[
                    { id: \"new\", label: \"New Item\", onClick: () => {} },
                    { id: \"sync\", label: \"Sync\", onClick: () => {} },
                ]}
            />
            <SettingsPanel
                title=\"Preferences\"
                fields={[
                    { id: \"notifications\", label: \"Notifications\", value: \"enabled\" },
                    { id: \"visibility\", label: \"Visibility\", value: \"team\" },
                ]}
            />
        </div>
    );
}
"""


class Command(BaseCommand):
    help = "Create a new one-pager app scaffold with shared backend and URL wiring"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str, help="Django app name (snake_case)")
        parser.add_argument("--slug", type=str, default=None, help="Base URL slug; defaults to app_name")
        parser.add_argument(
            "--no-wire",
            action="store_true",
            help="Create files but do not update INSTALLED_APPS or root URLs",
        )

    def handle(self, *args, **options):
        app_name = options["app_name"].strip()
        slug = (options["slug"] or app_name).strip().strip("/")
        should_wire = not options["no_wire"]

        self._validate_identifier(app_name)
        self._validate_slug(slug)

        base_dir = Path(settings.BASE_DIR)
        app_dir = base_dir / app_name
        if app_dir.exists():
            raise CommandError(f"App directory already exists: {app_dir}")

        class_name = "".join(part.capitalize() for part in app_name.split("_")) + "Config"
        model_name = "".join(part.capitalize() for part in app_name.split("_")) + "Item"
        page_name = "".join(part.capitalize() for part in app_name.split("_"))

        self._create_app_files(app_dir, app_name, slug, class_name, model_name)
        self._create_frontend_files(base_dir, app_name, slug, page_name)
        blueprint_summary = sync_presentation_blueprints(base_dir)

        if should_wire:
            self._wire_settings(base_dir / "gr_project" / "settings.py", app_name)
            self._wire_urls(base_dir / "gr_project" / "urls.py", app_name, slug)

        self.stdout.write(self.style.SUCCESS(f"Created scaffold for '{app_name}' at {app_dir}"))
        if should_wire:
            self.stdout.write(self.style.SUCCESS("Wired app into settings and root URLs."))
        self.stdout.write(
            self.style.SUCCESS(
                "Synced MDX presentation blueprints: "
                f"slides={blueprint_summary['slide_count']} tags={blueprint_summary['tag_count']}"
            )
        )
        self.stdout.write(
            "Next: run migrations and tests -> "
            f"./a_gr_venv/bin/python manage.py makemigrations {app_name} && "
            f"./a_gr_venv/bin/python manage.py migrate && "
            f"./a_gr_venv/bin/python manage.py test {app_name}"
        )

    def _validate_identifier(self, value):
        if not re.fullmatch(r"[a-z][a-z0-9_]*", value):
            raise CommandError("app_name must be snake_case and start with a letter.")
        if keyword.iskeyword(value):
            raise CommandError("app_name cannot be a Python keyword.")

    def _validate_slug(self, value):
        if not re.fullmatch(r"[a-z0-9-]+", value):
            raise CommandError("slug must use lowercase letters, numbers, and dashes only.")

    def _create_app_files(self, app_dir, app_name, slug, class_name, model_name):
        (app_dir / "migrations").mkdir(parents=True)
        (app_dir / "migrations" / "__init__.py").write_text("", encoding="utf-8")
        model_snake = re.sub(r"(?<!^)(?=[A-Z])", "_", model_name).lower()

        files = {
            "__init__.py": "",
            "apps.py": APP_CONFIG_TEMPLATE.format(class_name=class_name, app_name=app_name),
            "models.py": MODELS_TEMPLATE.format(model_name=model_name, model_snake=model_snake),
            "serializers.py": SERIALIZERS_TEMPLATE.format(model_name=model_name),
            "permissions.py": PERMISSIONS_TEMPLATE.format(model_name=model_name),
            "views.py": VIEWS_TEMPLATE.format(model_name=model_name),
            "urls.py": URLS_TEMPLATE.format(model_name=model_name, slug=slug),
            "admin.py": ADMIN_TEMPLATE.format(model_name=model_name),
            "tests.py": TESTS_TEMPLATE.format(model_name=model_name, slug=slug),
        }

        for file_name, content in files.items():
            (app_dir / file_name).write_text(content, encoding="utf-8")

    def _create_frontend_files(self, base_dir, app_name, slug, page_name):
        frontend_base = base_dir / "ui_apps" / app_name
        pages_dir = frontend_base / "pages"
        pages_dir.mkdir(parents=True)

        route_file = frontend_base / "route.tsx"
        page_file = pages_dir / f"{page_name}Page.tsx"

        route_content = FRONTEND_ROUTE_TEMPLATE.replace("__PAGE_NAME__", page_name).replace("__SLUG__", slug)
        page_content = FRONTEND_PAGE_TEMPLATE.replace("__PAGE_NAME__", page_name)

        route_file.write_text(
            route_content,
            encoding="utf-8",
        )
        page_file.write_text(
            page_content,
            encoding="utf-8",
        )

    def _wire_settings(self, settings_path, app_name):
        source = settings_path.read_text(encoding="utf-8")
        app_config = f"'{app_name}.apps.{''.join(part.capitalize() for part in app_name.split('_'))}Config'"

        if app_config in source:
            return

        marker = "    'platform_core.apps.PlatformCoreConfig',\n"
        if marker not in source:
            raise CommandError("Unable to find insertion marker in settings.py")

        source = source.replace(marker, marker + f"    {app_config},\n")
        settings_path.write_text(source, encoding="utf-8")

    def _wire_urls(self, urls_path, app_name, slug):
        source = urls_path.read_text(encoding="utf-8")
        insert_line = f"    path('{slug}/', include('{app_name}.urls')),\n"

        if insert_line in source:
            return

        marker = "] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)"
        if marker not in source:
            raise CommandError("Unable to find URL insertion marker in gr_project/urls.py")

        source = source.replace(
            marker,
            insert_line + marker,
        )
        urls_path.write_text(source, encoding="utf-8")
