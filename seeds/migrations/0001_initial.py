from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
        ("peringram", "0007_alter_industrygroup_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="Idea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("raw_content", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[("RAW", "Raw"), ("SEED", "Seed"), ("BUSINESS", "Business")],
                        default="RAW",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "industry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ideas",
                        to="peringram.industry",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ideas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="Seed",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("polish_notes", models.JSONField(blank=True, default=dict)),
                ("germination_date", models.DateField(auto_now_add=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "idea",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seed",
                        to="seeds.idea",
                    ),
                ),
            ],
            options={"ordering": ["-germination_date", "-updated_at"]},
        ),
        migrations.CreateModel(
            name="Business",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("brand_name", models.CharField(max_length=160)),
                ("market_status", models.CharField(max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "seed",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="business",
                        to="seeds.seed",
                    ),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
    ]
