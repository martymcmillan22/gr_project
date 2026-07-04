from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import platform_core.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("platform_core", "0009_customer_tenant_memberships"),
    ]

    operations = [
        migrations.AddField(
            model_name="contractbillingnotification",
            name="last_attempt_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="contractbillingnotification",
            name="last_error",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="contractbillingnotification",
            name="next_retry_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="contractbillingnotification",
            name="retry_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="ContractBillingAccessLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("link_key", models.CharField(default=platform_core.models._billing_access_link_key, max_length=32, unique=True)),
                ("tenant_key", models.CharField(default="default", max_length=120)),
                ("client_key", models.CharField(default="all", max_length=120)),
                ("window_days", models.PositiveIntegerField(default=30)),
                ("label", models.CharField(blank=True, default="", max_length=120)),
                ("recipient_email", models.EmailField(blank=True, default="", max_length=254)),
                ("is_active", models.BooleanField(default=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("use_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contract_billing_access_links",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Contract Billing Access Link",
                "verbose_name_plural": "Contract Billing Access Links",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="contractbillingaccesslink",
            index=models.Index(fields=["tenant_key", "client_key", "created_at"], name="platform_cor_tenant__a643b4_idx"),
        ),
        migrations.AddIndex(
            model_name="contractbillingaccesslink",
            index=models.Index(fields=["is_active", "expires_at"], name="platform_cor_is_acti_049908_idx"),
        ),
    ]
