from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0010_semantic_integration_model"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticAnalyticsSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("metrics", models.JSONField(default=dict)),
                ("project_count", models.PositiveIntegerField(default=0)),
                ("drift_mean", models.FloatField(default=0.0)),
                ("drift_std", models.FloatField(default=0.0)),
                ("confidence_mean", models.FloatField(default=0.0)),
                ("confidence_std", models.FloatField(default=0.0)),
                ("stability_mean", models.FloatField(default=0.0)),
                ("stability_std", models.FloatField(default=0.0)),
                ("lineage_cluster_map", models.JSONField(default=dict)),
                ("tag_frequency_map", models.JSONField(default=dict)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="SemanticAgentRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("agent_name", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(choices=[("completed", "Completed"), ("failed", "Failed")], default="completed", max_length=20)),
                ("actions_taken", models.JSONField(blank=True, default=list)),
                ("insights_generated", models.JSONField(blank=True, default=list)),
                ("error_message", models.TextField(blank=True)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
