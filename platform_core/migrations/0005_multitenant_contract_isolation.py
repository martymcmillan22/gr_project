from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0004_contractusageevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientcontractprofile",
            name="tenant_key",
            field=models.CharField(default="default", max_length=120),
        ),
        migrations.AlterField(
            model_name="clientcontractprofile",
            name="client_key",
            field=models.CharField(max_length=120),
        ),
        migrations.AddConstraint(
            model_name="clientcontractprofile",
            constraint=models.UniqueConstraint(fields=("tenant_key", "client_key"), name="uniq_contract_profile_tenant_client"),
        ),
        migrations.AddField(
            model_name="contractusageevent",
            name="tenant_key",
            field=models.CharField(blank=True, default="default", max_length=120),
        ),
        migrations.AddIndex(
            model_name="contractusageevent",
            index=models.Index(fields=["tenant_key", "created_at"], name="platform_cor_tenant__7628ec_idx"),
        ),
    ]
