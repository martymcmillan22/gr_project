from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("platform_core", "0008_billing_access_jobs_notifications"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerTenantMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tenant_key", models.CharField(max_length=120)),
                ("client_key", models.CharField(default="all", max_length=120)),
                ("role", models.CharField(choices=[("viewer", "Viewer"), ("billing", "Billing"), ("owner", "Owner")], default="viewer", max_length=16)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="customer_tenant_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Customer Tenant Membership",
                "verbose_name_plural": "Customer Tenant Memberships",
                "ordering": ["tenant_key", "client_key", "user_id"],
            },
        ),
        migrations.AddConstraint(
            model_name="customertenantmembership",
            constraint=models.UniqueConstraint(fields=("user", "tenant_key", "client_key"), name="uniq_customer_tenant_membership"),
        ),
    ]
