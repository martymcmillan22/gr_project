from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0002_insightsnarrativesnapshot"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClientContractProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("client_key", models.CharField(max_length=120, unique=True)),
                ("display_name", models.CharField(blank=True, default="", max_length=160)),
                ("default_schema_version", models.CharField(blank=True, default="", max_length=16)),
                ("default_capabilities", models.TextField(blank=True, default="")),
                ("strict_negotiation", models.BooleanField(default=False)),
                ("strict_payload_shape", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Client Contract Profile",
                "verbose_name_plural": "Client Contract Profiles",
                "ordering": ["client_key"],
            },
        ),
    ]
