from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("platform_core", "0007_contract_billing_snapshots"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientcontractprofile",
            name="billing_contact_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.CreateModel(
            name="ContractBillingJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tenant_key", models.CharField(default="default", max_length=120)),
                ("client_key", models.CharField(default="all", max_length=120)),
                ("job_type", models.CharField(choices=[("billing_cycle", "Billing cycle"), ("invoice_export", "Invoice export"), ("notify", "Notify")], default="billing_cycle", max_length=32)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=16)),
                ("payload", models.JSONField(default=dict)),
                ("result_payload", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("requested_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="contract_billing_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Contract Billing Job",
                "verbose_name_plural": "Contract Billing Jobs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ContractBillingNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tenant_key", models.CharField(default="default", max_length=120)),
                ("client_key", models.CharField(default="all", max_length=120)),
                ("channel", models.CharField(default="email", max_length=24)),
                ("recipient", models.EmailField(blank=True, default="", max_length=254)),
                ("subject", models.CharField(blank=True, default="", max_length=255)),
                ("body", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("queued", "Queued"), ("sent", "Sent"), ("skipped", "Skipped"), ("failed", "Failed")], default="queued", max_length=16)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("related_job", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notifications", to="platform_core.contractbillingjob")),
            ],
            options={
                "verbose_name": "Contract Billing Notification",
                "verbose_name_plural": "Contract Billing Notifications",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="contractbillingjob",
            index=models.Index(fields=["status", "created_at"], name="platform_cor_status__2d5014_idx"),
        ),
        migrations.AddIndex(
            model_name="contractbillingjob",
            index=models.Index(fields=["tenant_key", "client_key", "created_at"], name="platform_cor_tenant__13bfef_idx"),
        ),
        migrations.AddIndex(
            model_name="contractbillingnotification",
            index=models.Index(fields=["status", "created_at"], name="platform_cor_status__9613d6_idx"),
        ),
        migrations.AddIndex(
            model_name="contractbillingnotification",
            index=models.Index(fields=["tenant_key", "client_key", "created_at"], name="platform_cor_tenant__a83de9_idx"),
        ),
    ]
