from django.conf import settings
from django.db import migrations, models


def create_initial_bundle_revisions(apps, schema_editor):
    SemanticBundle = apps.get_model("platform_core", "SemanticBundle")
    SemanticBundleRevision = apps.get_model("platform_core", "SemanticBundleRevision")

    for bundle in SemanticBundle.objects.all():
        SemanticBundleRevision.objects.get_or_create(
            bundle=bundle,
            revision_number=1,
            defaults={
                "label": bundle.label,
                "family": bundle.family,
                "description": bundle.description,
                "sequence": bundle.sequence,
                "created_by_id": bundle.created_by_id,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("platform_core", "0013_semanticbundle"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticBundleRevision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("revision_number", models.PositiveIntegerField()),
                ("label", models.CharField(max_length=160)),
                ("family", models.CharField(db_index=True, max_length=80)),
                ("description", models.TextField(blank=True, default="")),
                ("sequence", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "bundle",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="revisions", to="platform_core.semanticbundle"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="semantic_bundle_revisions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-revision_number", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="semanticbundlerevision",
            constraint=models.UniqueConstraint(fields=("bundle", "revision_number"), name="platform_co_bundle_revision_unique"),
        ),
        migrations.AddIndex(
            model_name="semanticbundlerevision",
            index=models.Index(fields=["bundle", "revision_number"], name="platform_co_bundle__4dc235_idx"),
        ),
        migrations.RunPython(create_initial_bundle_revisions, migrations.RunPython.noop),
    ]