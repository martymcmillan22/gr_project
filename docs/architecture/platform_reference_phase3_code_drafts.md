# Platform Reference Phase 3 Code Drafts

## Purpose

This document contains the exact draft code for Phase 3 Step 3.2 and the exact draft migration contents for:

- `platform_reference/migrations/0001_initial_reference_tables.py`
- `platform_reference/migrations/0002_copy_reference_data_from_platform_core.py`

These are draft artifacts only.

- They are not active runtime code.
- They do not mutate schema.
- They do not create tables.
- They exist for review before any `makemigrations` or `migrate` command is run.

## Draft 1: Transitional Model Code For Step 3.2

Target file when Phase 3 execution begins:

- `platform_reference/models.py`

Draft content:

```python
from django.db import models


class NAICSReference(models.Model):
    code = models.CharField(max_length=12, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    sector_code = models.CharField(max_length=12, blank=True, default="")
    source_version = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "platform_core_naicsreference"
        ordering = ["code"]

    def __str__(self):
        return f"NAICS {self.code} {self.title}".strip()


class GICSReference(models.Model):
    LEVEL_SECTOR = "sector"
    LEVEL_INDUSTRY_GROUP = "industry_group"
    LEVEL_INDUSTRY = "industry"
    LEVEL_SUB_INDUSTRY = "sub_industry"
    LEVEL_CHOICES = [
        (LEVEL_SECTOR, "Sector"),
        (LEVEL_INDUSTRY_GROUP, "Industry Group"),
        (LEVEL_INDUSTRY, "Industry"),
        (LEVEL_SUB_INDUSTRY, "Sub-Industry"),
    ]

    code = models.CharField(max_length=24, db_index=True)
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=24, choices=LEVEL_CHOICES, default=LEVEL_SUB_INDUSTRY, db_index=True)
    parent_code = models.CharField(max_length=24, blank=True, default="")
    description = models.TextField(blank=True, default="")
    source_version = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "platform_core_gicsreference"
        ordering = ["level", "code"]

    def __str__(self):
        return f"GICS {self.level} {self.code} {self.name}".strip()


class PlatformReferenceNAICSReferenceSchema(models.Model):
    code = models.CharField(max_length=12, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    sector_code = models.CharField(max_length=12, blank=True, default="")
    source_version = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "platform_reference_naicsreference"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["sector_code", "code"], name="platform_re_sector__naics_idx"),
            models.Index(fields=["is_active", "code"], name="pr_naics_active_code_idx"),
        ]

    def __str__(self):
        return f"NAICS {self.code} {self.title}".strip()


class PlatformReferenceGICSReferenceSchema(models.Model):
    LEVEL_SECTOR = "sector"
    LEVEL_INDUSTRY_GROUP = "industry_group"
    LEVEL_INDUSTRY = "industry"
    LEVEL_SUB_INDUSTRY = "sub_industry"
    LEVEL_CHOICES = [
        (LEVEL_SECTOR, "Sector"),
        (LEVEL_INDUSTRY_GROUP, "Industry Group"),
        (LEVEL_INDUSTRY, "Industry"),
        (LEVEL_SUB_INDUSTRY, "Sub-Industry"),
    ]

    code = models.CharField(max_length=24, db_index=True)
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=24, choices=LEVEL_CHOICES, default=LEVEL_SUB_INDUSTRY, db_index=True)
    parent_code = models.CharField(max_length=24, blank=True, default="")
    description = models.TextField(blank=True, default="")
    source_version = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "platform_reference_gicsreference"
        ordering = ["level", "code"]
        constraints = [
            models.UniqueConstraint(fields=["code", "level"], name="platform_re_gics_code_level_unique"),
        ]
        indexes = [
            models.Index(fields=["level", "code"], name="platform_re_level_gics_idx"),
            models.Index(fields=["parent_code", "level"], name="pr_gics_parent_level_idx"),
            models.Index(fields=["is_active", "level", "code"], name="platform_re_is_active_gics_idx"),
        ]

    def __str__(self):
        return f"GICS {self.level} {self.code} {self.name}".strip()
```

### Notes on the transitional model draft

- The bridge classes keep runtime pointed at `platform_core_*` tables.
- The `PlatformReference*Schema` classes exist only to generate the future schema.
- They intentionally avoid name collision with the live bridge classes.

## Draft 2: `platform_reference/migrations/0001_initial_reference_tables.py`

Draft content:

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PlatformReferenceGICSReferenceSchema",
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
                "db_table": "platform_reference_gicsreference",
                "ordering": ["level", "code"],
                "indexes": [
                    models.Index(fields=["level", "code"], name="platform_re_level_gics_idx"),
                    models.Index(fields=["parent_code", "level"], name="pr_gics_parent_level_idx"),
                    models.Index(fields=["is_active", "level", "code"], name="platform_re_is_active_gics_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("code", "level"), name="platform_re_gics_code_level_unique"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PlatformReferenceNAICSReferenceSchema",
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
                "db_table": "platform_reference_naicsreference",
                "ordering": ["code"],
                "indexes": [
                    models.Index(fields=["sector_code", "code"], name="platform_re_sector__naics_idx"),
                    models.Index(fields=["is_active", "code"], name="pr_naics_active_code_idx"),
                ],
            },
        ),
    ]
```

## Draft 3: `platform_reference/migrations/0002_copy_reference_data_from_platform_core.py`

Draft content:

```python
from django.db import migrations


def copy_reference_data(apps, schema_editor):
    OldGICS = apps.get_model("platform_core", "GICSReference")
    OldNAICS = apps.get_model("platform_core", "NAICSReference")
    NewGICSSchema = apps.get_model("platform_reference", "PlatformReferenceGICSReferenceSchema")
    NewNAICSSchema = apps.get_model("platform_reference", "PlatformReferenceNAICSReferenceSchema")

    for row in OldGICS.objects.order_by("id").iterator():
        NewGICSSchema.objects.update_or_create(
            id=row.id,
            defaults={
                "code": row.code,
                "name": row.name,
                "level": row.level,
                "parent_code": row.parent_code,
                "description": row.description,
                "source_version": row.source_version,
                "is_active": row.is_active,
                "updated_at": row.updated_at,
                "created_at": row.created_at,
            },
        )

    for row in OldNAICS.objects.order_by("id").iterator():
        NewNAICSSchema.objects.update_or_create(
            id=row.id,
            defaults={
                "code": row.code,
                "title": row.title,
                "description": row.description,
                "sector_code": row.sector_code,
                "source_version": row.source_version,
                "is_active": row.is_active,
                "updated_at": row.updated_at,
                "created_at": row.created_at,
            },
        )


def reverse_copy_reference_data(apps, schema_editor):
    NewGICSSchema = apps.get_model("platform_reference", "PlatformReferenceGICSReferenceSchema")
    NewNAICSSchema = apps.get_model("platform_reference", "PlatformReferenceNAICSReferenceSchema")

    # Safe only before runtime bridge models are flipped to platform_reference_* tables.
    # After cutover, do not reverse this migration without an explicit rollback plan.
    NewGICSSchema.objects.all().delete()
    NewNAICSSchema.objects.all().delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("platform_reference", "0001_initial_reference_tables"),
        ("platform_core", "0019_rename_platform_co_level_3b70f8_idx_platform_co_level_60ea83_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_reference_data, reverse_copy_reference_data),
    ]
```

### Notes on the copy migration draft

- It preserves `id` and timestamps.
- It iterates deterministically by `id`.
- It uses `update_or_create` for restart safety.
- It uses `atomic = False` to avoid one oversized transaction during data copy.
- Its reverse operation clears only the new target tables and is safe only before the runtime table flip.
- After runtime cutover, reversal should be treated as a separate operational rollback, not a casual migration reverse.

## Optional Draft 4: `platform_core/migrations/0020_drop_reference_tables_after_platform_reference_cutover.py`

This draft is intentionally destructive and must be treated as a runbook artifact, not a routine migration candidate.

### Irreversible marker

- This is the first step in the sequence that can permanently remove the old reference tables.
- Do not apply it until the runtime has already been stable on `platform_reference_*` tables.
- Do not apply it without explicit operator confirmation immediately before execution.

### Required dependency chain

This draft assumes all of the following are already complete:

1. `platform_reference/migrations/0001_initial_reference_tables.py` applied
2. `platform_reference/migrations/0002_copy_reference_data_from_platform_core.py` applied
3. runtime bridge models flipped to `platform_reference_*` tables
4. focused runtime validation re-run successfully on the new physical tables

### Required pre-drop validation checklist

Before applying the cleanup migration, verify all of the following:

- `./a_gr_venv/bin/python manage.py check`
- `./a_gr_venv/bin/python manage.py test platform_core.tests_reference_promotion_gate_command`
- `./a_gr_venv/bin/python manage.py test platform_core.tests_mlas_executive_console`
- `./a_gr_venv/bin/python manage.py reference_load_naics_snapshot`

And perform explicit data/state checks:

- row counts match between old and new tables
- ordered `id` continuity matches between old and new tables
- sampled rows match for GICS and NAICS content
- current runtime reads and writes hit `platform_reference_*` tables only
- no unresolved SQL/reporting dependence remains on `platform_core_*` tables

### Draft migration body

```python
from django.db import migrations


class Migration(migrations.Migration):
    # IRREVERSIBLE BOUNDARY:
    # This migration deletes the old platform_core reference table models after
    # the application has already been cut over to platform_reference_* tables.
    dependencies = [
        ("platform_core", "0019_rename_platform_co_level_3b70f8_idx_platform_co_level_60ea83_idx_and_more"),
        ("platform_reference", "0002_copy_reference_data_from_platform_core"),
    ]

    operations = [
        # Destructive boundary: apply only after runtime has been stable on
        # platform_reference_* tables and explicit approval has been given.
        migrations.DeleteModel(name="GICSReference"),
        migrations.DeleteModel(name="NAICSReference"),
    ]
```

### Rollback checkpoint

- Last low-risk rollback point is immediately before applying this migration.
- After this migration is applied, rollback is no longer a simple code revert.
- Expect recovery to require schema restoration from backup or a compensating migration plan.

### Operator warnings

- Treat this as a stop-and-confirm boundary.
- Prefer a schema backup and data backup before execution.
- Prefer execution during a controlled maintenance window if the environment is shared.
- Do not chain this cleanup with unrelated migrations.

Do not apply a cleanup migration like this until the runtime has already been running successfully on `platform_reference_*` tables and you explicitly approve destructive cleanup.
