from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0020_reference_tables_deprecation_state_marker"),
        ("platform_reference", "0002_copy_reference_data_from_platform_core"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP TABLE IF EXISTS platform_core_gicsreference;",
                "DROP TABLE IF EXISTS platform_core_naicsreference;",
            ],
            reverse_sql=[
                (
                    "CREATE TABLE IF NOT EXISTS platform_core_gicsreference ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "code VARCHAR(24) NOT NULL, "
                    "name VARCHAR(255) NOT NULL, "
                    "level VARCHAR(24) NOT NULL, "
                    "parent_code VARCHAR(24) NOT NULL DEFAULT '', "
                    "description TEXT NOT NULL DEFAULT '', "
                    "source_version VARCHAR(32) NOT NULL DEFAULT '', "
                    "is_active BOOLEAN NOT NULL DEFAULT 1, "
                    "updated_at DATETIME NOT NULL, "
                    "created_at DATETIME NOT NULL"
                    ");"
                ),
                "CREATE UNIQUE INDEX IF NOT EXISTS platform_co_gics_code_level_unique ON platform_core_gicsreference (code, level);",
                "CREATE INDEX IF NOT EXISTS platform_co_level_60ea83_idx ON platform_core_gicsreference (level, code);",
                "CREATE INDEX IF NOT EXISTS platform_co_parent__1e8635_idx ON platform_core_gicsreference (parent_code, level);",
                "CREATE INDEX IF NOT EXISTS platform_co_is_acti_8d8970_idx ON platform_core_gicsreference (is_active, level, code);",
                (
                    "CREATE TABLE IF NOT EXISTS platform_core_naicsreference ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "code VARCHAR(12) NOT NULL UNIQUE, "
                    "title VARCHAR(255) NOT NULL, "
                    "description TEXT NOT NULL DEFAULT '', "
                    "sector_code VARCHAR(12) NOT NULL DEFAULT '', "
                    "source_version VARCHAR(32) NOT NULL DEFAULT '', "
                    "is_active BOOLEAN NOT NULL DEFAULT 1, "
                    "updated_at DATETIME NOT NULL, "
                    "created_at DATETIME NOT NULL"
                    ");"
                ),
                "CREATE INDEX IF NOT EXISTS platform_co_sector__ed90db_idx ON platform_core_naicsreference (sector_code, code);",
                "CREATE INDEX IF NOT EXISTS platform_co_is_acti_e6ca9e_idx ON platform_core_naicsreference (is_active, code);",
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="GICSReference"),
                migrations.DeleteModel(name="NAICSReference"),
            ],
        ),
    ]
