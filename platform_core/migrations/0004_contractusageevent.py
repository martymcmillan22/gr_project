from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0003_clientcontractprofile"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContractUsageEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("client_key", models.CharField(blank=True, default="anonymous", max_length=120)),
                ("endpoint", models.CharField(max_length=80)),
                ("requested_schema_version", models.CharField(blank=True, default="", max_length=32)),
                ("selected_schema_version", models.CharField(blank=True, default="", max_length=32)),
                ("negotiation_source", models.CharField(blank=True, default="", max_length=32)),
                ("strict_negotiation", models.BooleanField(default=False)),
                ("strict_payload_shape", models.BooleanField(default=False)),
                ("period", models.CharField(blank=True, default="", max_length=24)),
                ("output_format", models.CharField(blank=True, default="", max_length=24)),
                ("status_code", models.PositiveSmallIntegerField(default=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Contract Usage Event",
                "verbose_name_plural": "Contract Usage Events",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="contractusageevent",
            index=models.Index(fields=["client_key", "created_at"], name="platform_cor_client__9f5ec8_idx"),
        ),
        migrations.AddIndex(
            model_name="contractusageevent",
            index=models.Index(fields=["endpoint", "created_at"], name="platform_cor_endpoin_ef8a5f_idx"),
        ),
        migrations.AddIndex(
            model_name="contractusageevent",
            index=models.Index(fields=["status_code", "created_at"], name="platform_cor_status__51db4e_idx"),
        ),
    ]
