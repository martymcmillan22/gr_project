from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_subscription_tier"),
    ]

    operations = [
        migrations.CreateModel(
            name="BillingWebhookEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(default="generic", max_length=32)),
                ("provider_event_id", models.CharField(blank=True, max_length=128)),
                ("idempotency_key", models.CharField(max_length=128)),
                ("event_type", models.CharField(blank=True, max_length=128)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("received", "Received"),
                            ("processed", "Processed"),
                            ("ignored", "Ignored"),
                            ("failed", "Failed"),
                        ],
                        default="received",
                        max_length=16,
                    ),
                ),
                ("signature_valid", models.BooleanField(default=False)),
                ("target_tier", models.CharField(blank=True, max_length=32)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="billing_webhook_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
        migrations.AddConstraint(
            model_name="billingwebhookevent",
            constraint=models.UniqueConstraint(
                fields=("provider", "idempotency_key"),
                name="ux_billing_webhook_event_provider_idempotency",
            ),
        ),
    ]
