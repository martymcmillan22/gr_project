from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0019_rename_platform_co_level_3b70f8_idx_platform_co_level_60ea83_idx_and_more"),
        ("platform_reference", "0002_copy_reference_data_from_platform_core"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelOptions(
                    name="gicsreference",
                    options={
                        "managed": False,
                        "ordering": ["level", "code"],
                        "verbose_name": "DEPRECATED Legacy GICS Reference",
                        "verbose_name_plural": "DEPRECATED Legacy GICS References",
                    },
                ),
                migrations.AlterModelOptions(
                    name="naicsreference",
                    options={
                        "managed": False,
                        "ordering": ["code"],
                        "verbose_name": "DEPRECATED Legacy NAICS Reference",
                        "verbose_name_plural": "DEPRECATED Legacy NAICS References",
                    },
                ),
            ],
        ),
    ]
