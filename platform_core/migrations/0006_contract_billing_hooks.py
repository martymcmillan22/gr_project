from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0005_multitenant_contract_isolation"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientcontractprofile",
            name="billing_plan",
            field=models.CharField(blank=True, default="standard", max_length=32),
        ),
        migrations.AddField(
            model_name="clientcontractprofile",
            name="monthly_event_allowance",
            field=models.PositiveIntegerField(default=1000),
        ),
        migrations.AddField(
            model_name="clientcontractprofile",
            name="overage_rate",
            field=models.DecimalField(decimal_places=4, default=Decimal("0.0100"), max_digits=8),
        ),
        migrations.AddField(
            model_name="contractusageevent",
            name="billable_amount",
            field=models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=10),
        ),
        migrations.AddField(
            model_name="contractusageevent",
            name="billable_category",
            field=models.CharField(blank=True, default="contract_api", max_length=32),
        ),
        migrations.AddField(
            model_name="contractusageevent",
            name="billable_units",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
