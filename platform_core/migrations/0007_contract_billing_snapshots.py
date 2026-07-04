from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0006_contract_billing_hooks"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContractBillingSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tenant_key", models.CharField(default="default", max_length=120)),
                ("client_key", models.CharField(default="all", max_length=120)),
                ("window_days", models.PositiveIntegerField(default=30)),
                ("period_start", models.DateTimeField()),
                ("period_end", models.DateTimeField()),
                ("summary_payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Contract Billing Snapshot",
                "verbose_name_plural": "Contract Billing Snapshots",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="contractbillingsnapshot",
            index=models.Index(fields=["tenant_key", "client_key", "created_at"], name="platform_cor_tenant__44efe6_idx"),
        ),
    ]
