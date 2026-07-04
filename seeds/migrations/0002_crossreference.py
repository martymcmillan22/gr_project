from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("seeds", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CrossReference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "relationship_type",
                    models.CharField(
                        choices=[
                            ("similar", "Similar"),
                            ("supplies", "Supplies"),
                            ("depends_on", "Depends On"),
                            ("complements", "Complements"),
                        ],
                        max_length=32,
                    ),
                ),
                ("score", models.DecimalField(decimal_places=5, default=0.0, max_digits=6)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "source_business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outgoing_cross_references",
                        to="seeds.business",
                    ),
                ),
                (
                    "target_business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="incoming_cross_references",
                        to="seeds.business",
                    ),
                ),
            ],
            options={"ordering": ["-score", "-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="crossreference",
            constraint=models.UniqueConstraint(
                fields=("source_business", "target_business", "relationship_type"),
                name="ux_cr_source_target_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="crossreference",
            constraint=models.CheckConstraint(
                condition=models.Q(("source_business", models.F("target_business")), _negated=True),
                name="ck_cr_no_self_reference",
            ),
        ),
    ]
