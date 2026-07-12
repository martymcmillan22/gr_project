from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0004_semanticlineagerecord"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectevolutionsnapshot",
            name="schema_issue_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="SemanticAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alert_type", models.CharField(choices=[("high_drift", "High Drift"), ("low_confidence", "Low Confidence"), ("unstable_stability", "Unstable Stability"), ("schema_failure", "Schema Failure"), ("repeated_schema_failure", "Repeated Schema Failure"), ("timeline_drift_trend", "Timeline Drift Trend")], max_length=64)),
                ("severity", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], max_length=20)),
                ("message", models.CharField(max_length=500)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="semantic_alerts",
                        to="project_middle_layer.projectnode",
                    ),
                ),
                (
                    "source_snapshot",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="semantic_alerts",
                        to="project_middle_layer.projectevolutionsnapshot",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
