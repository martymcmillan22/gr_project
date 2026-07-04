from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0014_semanticbundlerevision"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticBundleShare",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("permission", models.CharField(choices=[("view", "View"), ("edit", "Edit")], default="view", max_length=12)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "bundle",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shares", to="platform_core.semanticbundle"),
                ),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="semantic_bundle_shares_created", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="semantic_bundle_shares", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "indexes": [models.Index(fields=["bundle", "permission", "is_active"], name="platform_co_bundle__0a8a2f_idx")],
                "constraints": [models.UniqueConstraint(fields=("bundle", "user"), name="platform_co_bundle_share_unique")],
            },
        ),
        migrations.CreateModel(
            name="SemanticBundleRevisionTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64)),
                ("note", models.CharField(blank=True, default="", max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "bundle",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="revision_tags", to="platform_core.semanticbundle"),
                ),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="semantic_bundle_revision_tags", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "revision",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tags", to="platform_core.semanticbundlerevision"),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["bundle", "name"], name="platform_co_bundle__29f6ff_idx"),
                    models.Index(fields=["bundle", "revision"], name="platform_co_bundle__78d723_idx"),
                ],
                "constraints": [models.UniqueConstraint(fields=("bundle", "name"), name="platform_co_bundle_revision_tag_unique")],
            },
        ),
    ]
