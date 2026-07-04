from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0017_mlasclassificationrecord"),
    ]

    operations = [
        migrations.CreateModel(
            name="GICSReference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=24)),
                ("name", models.CharField(max_length=255)),
                (
                    "level",
                    models.CharField(
                        choices=[
                            ("sector", "Sector"),
                            ("industry_group", "Industry Group"),
                            ("industry", "Industry"),
                            ("sub_industry", "Sub-Industry"),
                        ],
                        db_index=True,
                        default="sub_industry",
                        max_length=24,
                    ),
                ),
                ("parent_code", models.CharField(blank=True, default="", max_length=24)),
                ("description", models.TextField(blank=True, default="")),
                ("source_version", models.CharField(blank=True, default="", max_length=32)),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["level", "code"],
                "indexes": [
                    models.Index(fields=["level", "code"], name="platform_co_level_3b70f8_idx"),
                    models.Index(fields=["parent_code", "level"], name="platform_co_parent__24ee9b_idx"),
                    models.Index(fields=["is_active", "level", "code"], name="platform_co_is_acti_f3ab40_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("code", "level"), name="platform_co_gics_code_level_unique"),
                ],
            },
        ),
        migrations.CreateModel(
            name="NAICSReference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=12, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("sector_code", models.CharField(blank=True, default="", max_length=12)),
                ("source_version", models.CharField(blank=True, default="", max_length=32)),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["code"],
                "indexes": [
                    models.Index(fields=["sector_code", "code"], name="platform_co_sector__99cb49_idx"),
                    models.Index(fields=["is_active", "code"], name="platform_co_is_acti_93dcb8_idx"),
                ],
            },
        ),
    ]
