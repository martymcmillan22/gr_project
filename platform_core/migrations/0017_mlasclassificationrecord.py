from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0016_quadrant_usage_event"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MLASClassificationRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("record_id", models.CharField(db_index=True, max_length=64, unique=True)),
                ("source_name_raw", models.CharField(max_length=255)),
                ("source_description_raw", models.TextField(blank=True, default="")),
                (
                    "target_layer",
                    models.CharField(
                        choices=[("term", "Term (64)"), ("meta", "MetaTerm (256)")],
                        default="term",
                        max_length=8,
                    ),
                ),
                ("mlas_subject_code", models.CharField(max_length=16)),
                ("mlas_branch_code", models.CharField(blank=True, default="", max_length=16)),
                ("mlas_term_code", models.CharField(blank=True, default="", max_length=16)),
                ("mlas_meta_term_code", models.CharField(blank=True, default="", max_length=16)),
                ("dewey_code", models.CharField(blank=True, default="", max_length=32)),
                ("gics_sector_code", models.CharField(blank=True, default="", max_length=32)),
                ("gics_industry_group_code", models.CharField(blank=True, default="", max_length=32)),
                ("gics_industry_code", models.CharField(blank=True, default="", max_length=32)),
                ("gics_sub_industry_code", models.CharField(blank=True, default="", max_length=32)),
                ("naics_code_2", models.CharField(blank=True, default="", max_length=8)),
                ("naics_code_3", models.CharField(blank=True, default="", max_length=8)),
                ("naics_code_4", models.CharField(blank=True, default="", max_length=8)),
                ("naics_code_5", models.CharField(blank=True, default="", max_length=8)),
                ("naics_code_6", models.CharField(blank=True, default="", max_length=8)),
                (
                    "algorithm_1_score",
                    models.FloatField(
                        default=0.0,
                        validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)],
                    ),
                ),
                (
                    "algorithm_2_score",
                    models.FloatField(
                        default=0.0,
                        validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)],
                    ),
                ),
                (
                    "algorithm_3_score",
                    models.FloatField(
                        default=0.0,
                        validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)],
                    ),
                ),
                (
                    "algorithm_4_score",
                    models.FloatField(
                        default=0.0,
                        validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)],
                    ),
                ),
                (
                    "algorithm_consensus_score",
                    models.FloatField(
                        default=0.0,
                        validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)],
                    ),
                ),
                ("quadrant_slug", models.CharField(blank=True, default="", max_length=64)),
                ("basetrue_label", models.CharField(blank=True, default="", max_length=160)),
                ("basetrue_description", models.TextField(blank=True, default="")),
                (
                    "confidence_overall",
                    models.FloatField(
                        default=0.0,
                        validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)],
                    ),
                ),
                ("confidence_reason", models.TextField(blank=True, default="")),
                (
                    "review_status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("candidate", "Candidate"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="mlas_classification_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["record_id"],
                "indexes": [
                    models.Index(fields=["review_status", "confidence_overall"], name="platform_co_review__72dbd8_idx"),
                    models.Index(fields=["mlas_subject_code", "mlas_branch_code", "mlas_term_code"], name="platform_co_mlas_s_f3c880_idx"),
                    models.Index(fields=["target_layer", "review_status"], name="platform_co_target__36cded_idx"),
                ],
            },
        ),
    ]
