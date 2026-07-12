from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0008_semantic_schedule_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticWebhook",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("target_url", models.URLField(max_length=500)),
                ("event_type", models.CharField(max_length=64)),
                ("secret_token", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(choices=[("active", "Active"), ("disabled", "Disabled")], default="active", max_length=20)),
                ("last_delivery", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="SemanticWebhookDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=64)),
                ("payload", models.JSONField(default=dict)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("delivered", "Delivered"), ("failed", "Failed")], default="pending", max_length=20)),
                ("response_code", models.IntegerField(blank=True, null=True)),
                ("response_body", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("webhook", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deliveries", to="project_middle_layer.semanticwebhook")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
