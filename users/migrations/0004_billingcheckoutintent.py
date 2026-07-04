from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_billingwebhookevent"),
    ]

    operations = [
        migrations.CreateModel(
            name="BillingCheckoutIntent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(default="stripe", max_length=32)),
                ("requested_tier", models.CharField(max_length=32)),
                ("idempotency_key", models.CharField(max_length=128)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("session_created", "Session Created"),
                            ("failed", "Failed"),
                            ("completed", "Completed"),
                        ],
                        default="created",
                        max_length=24,
                    ),
                ),
                ("provider_session_id", models.CharField(blank=True, max_length=128)),
                ("checkout_url", models.URLField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="billing_checkout_intents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
        migrations.AddConstraint(
            model_name="billingcheckoutintent",
            constraint=models.UniqueConstraint(
                fields=("user", "provider", "idempotency_key"),
                name="ux_billing_checkout_intent_user_provider_idempotency",
            ),
        ),
    ]
