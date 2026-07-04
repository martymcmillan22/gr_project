from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("platform_core", "0012_rename_platform_cor_tenant__a643b4_idx_platform_co_tenant__a4c302_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticBundle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=120, unique=True)),
                ("label", models.CharField(max_length=160)),
                ("family", models.CharField(db_index=True, max_length=80)),
                ("description", models.TextField(blank=True, default="")),
                ("sequence", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="semantic_bundles",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="semanticbundle",
            index=models.Index(fields=["family", "name"], name="platform_co_family_417313_idx"),
        ),
    ]