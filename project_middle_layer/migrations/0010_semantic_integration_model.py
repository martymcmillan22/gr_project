from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0009_semantic_webhook_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticIntegration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("direction", models.CharField(choices=[("inbound", "Inbound"), ("outbound", "Outbound"), ("bidirectional", "Bidirectional")], max_length=20)),
                ("target_system", models.CharField(max_length=120)),
                ("endpoint_url", models.URLField(blank=True, max_length=500)),
                ("api_key", models.CharField(max_length=64, unique=True)),
                ("permissions", models.JSONField(blank=True, default=list)),
                ("status", models.CharField(choices=[("active", "Active"), ("disabled", "Disabled")], default="active", max_length=20)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
    ]
