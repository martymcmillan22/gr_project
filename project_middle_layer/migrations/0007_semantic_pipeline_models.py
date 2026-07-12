from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0006_recommendations_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticPipeline",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("steps", models.JSONField(default=list)),
                ("triggers", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("last_run", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("idle", "Idle"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")],
                        default="idle",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="SemanticPipelineRun",
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
                    "pipeline",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="runs", to="project_middle_layer.semanticpipeline"),
                ),
            ],
            options={"ordering": ["-started_at", "-id"]},
        ),
    ]
