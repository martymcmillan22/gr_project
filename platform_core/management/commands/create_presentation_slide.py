from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from platform_core.presentation_mdx import sync_presentation_blueprints


SLIDE_TEMPLATE = """---
category: __CATEGORY__
labels: ui, blueprint
---

# __TITLE__

<LayoutGrid columns=\"2\" gap=\"16\">
  <Panel title=\"Primary Surface\" tone=\"primary\">
    <p>Describe the primary user intent for this screen.</p>
    <ComponentPreview component=\"DashboardCard\" status=\"draft\" />
  </Panel>
  <Panel title=\"Operational Surface\" tone=\"success\">
    <p>Describe operational controls and workflow transitions.</p>
    <ComponentPreview component=\"Taskboard\" status=\"planned\" />
  </Panel>
</LayoutGrid>

<LayoutGrid columns=\"2\" gap=\"12\">
  <Quadrant label=\"Q1: Discover\" emphasis=\"medium\">
    <p>Inputs and discovery context.</p>
    <ComponentPreview component=\"DiscoverPanel\" status=\"draft\" />
  </Quadrant>
  <Quadrant label=\"Q2: Decide\" emphasis=\"high\">
    <p>Decision support and key metrics.</p>
    <ComponentPreview component=\"DecisionPanel\" status=\"draft\" />
  </Quadrant>
  <Quadrant label=\"Q3: Execute\" emphasis=\"critical\">
    <p>Actions and execution controls.</p>
    <ComponentPreview component=\"ExecuteBoard\" status=\"draft\" />
  </Quadrant>
  <Quadrant label=\"Q4: Reflect\" emphasis=\"low\">
    <p>Retrospective and learning notes.</p>
    <ComponentPreview component=\"ReflectPanel\" status=\"draft\" />
  </Quadrant>
</LayoutGrid>
"""


def _slugify(value):
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


class Command(BaseCommand):
    help = "Create an MDX presentation slide blueprint and optionally sync generated React artifacts."

    def add_arguments(self, parser):
        parser.add_argument("slide_name", type=str, help="Slide name used as filename slug")
        parser.add_argument("--title", type=str, default="", help="Markdown heading title for the slide")
        parser.add_argument("--category", type=str, default="general", help="Slide category for registry grouping")
        parser.add_argument(
            "--no-sync",
            action="store_true",
            help="Create the slide file without running generation sync.",
        )

    def handle(self, *args, **options):
        raw_name = (options.get("slide_name") or "").strip()
        if not raw_name:
            raise CommandError("slide_name is required")

        slide_slug = _slugify(raw_name)
        if not slide_slug:
            raise CommandError("slide_name must include at least one alphanumeric character")

        title = (options.get("title") or "").strip() or " ".join(part.capitalize() for part in slide_slug.split("-"))
        category = _slugify((options.get("category") or "general").strip() or "general")

        slides_dir = Path(settings.BASE_DIR) / "docs" / "architecture" / "presentation" / "slides"
        slides_dir.mkdir(parents=True, exist_ok=True)

        slide_path = slides_dir / f"{slide_slug}.mdx"
        if slide_path.exists():
            raise CommandError(f"Slide already exists: {slide_path}")

        slide_content = (
            SLIDE_TEMPLATE.replace("__TITLE__", title)
            .replace("__CATEGORY__", category)
        )
        slide_path.write_text(slide_content, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Created slide blueprint: {slide_path}"))

        if options.get("no_sync"):
            return

        summary = sync_presentation_blueprints(Path(settings.BASE_DIR))
        self.stdout.write(
            self.style.SUCCESS(
                "Synced generated artifacts: "
                f"slides={summary['slide_count']} tags={summary['tag_count']} "
                f"frontend_out={summary['frontend_generated_dir']}"
            )
        )
