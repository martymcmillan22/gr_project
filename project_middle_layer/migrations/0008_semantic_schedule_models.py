from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0007_semantic_pipeline_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("cron_expression", models.CharField(default="0 0 * * *", max_length=64)),
                (
                    "action",
                    models.CharField(
                        choices=[("pipeline-run", "Pipeline Run"), ("export", "Export"), ("alert-check", "Alert Check")],
                        max_length=32,
                    ),
                ),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("is_paused", models.BooleanField(default=False)),
                ("last_run", models.DateTimeField(blank=True, null=True)),
                ("next_run", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("idle", "Idle"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed"), ("paused", "Paused")],
                        default="idle",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "pipeline",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="schedules", to="project_middle_layer.semanticpipeline"),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="SemanticScheduleRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("running", "Running"), ("completed", "Completed"), ("failed", "Failed")],
                        default="running",
                        max_length=20,
                    ),
                ),
                ("triggered_by", models.CharField(default="manual", max_length=120)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                (
                    "schedule",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="runs", to="project_middle_layer.semanticschedule"),
                ),
            ],
            options={"ordering": ["-started_at", "-id"]},
        ),
    ]
