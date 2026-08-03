# Platform Reference Phase 3 Execution Checklist

## Purpose

This checklist converts the Phase 3 physical database migration strategy into an execution-ready sequence for `GICSReference` and `NAICSReference`.

This document does not mutate schema by itself. It defines the exact filenames, app labels, migration ordering, code stubs, validation gates, and rollback points to use when Phase 3 execution begins.

## Scope

### Source app label

- `platform_core`

### Target app label

- `platform_reference`

### Source tables

- `platform_core_gicsreference`
- `platform_core_naicsreference`

### Target tables

- `platform_reference_gicsreference`
- `platform_reference_naicsreference`

## Execution Rules

- Do not run `makemigrations` until the future managed model definitions exist.
- Do not run `migrate` until the migration files are reviewed.
- Do not flip runtime `db_table` bindings until copy validation passes.
- Do not drop old `platform_core_*` tables until the app has already run successfully on `platform_reference_*` tables.

## Proposed Migration File Sequence

These are the exact filenames to use for the first Phase 3 cut.

### In `platform_reference/migrations/`

1. `0001_initial_reference_tables.py`
2. `0002_copy_reference_data_from_platform_core.py`

### In `platform_core/migrations/`

3. `0020_drop_reference_tables_after_platform_reference_cutover.py`

Notes:

- `platform_reference` currently has no real schema migrations for these models, so `0001_*` is the correct starting point there.
- `platform_core` currently ends at `0019_*`, so the cleanup migration should start at `0020_*`.

## Ordered Execution Checklist

### Step 3.1 Freeze the bridge

Status target:
- No code change required unless the bridge models drift.

Verify:
- `platform_reference.models` still points to:
  - `db_table = "platform_core_gicsreference"`
  - `db_table = "platform_core_naicsreference"`
  - `managed = False`

Validation:
- `./a_gr_venv/bin/python manage.py check`

Rollback:
- None needed if no code changed.

### Step 3.2 Add future managed models

Create future canonical managed models in `platform_reference.models` or a clearly separated transitional module.

Required properties:

- `managed = True`
- `db_table = "platform_reference_gicsreference"`
- `db_table = "platform_reference_naicsreference"`

Important constraint:

- Do not replace current runtime imports with these future models yet.
- Keep the current bridge models as the runtime surface until Step 3.5.

Implementation recommendation:

- Use clearly named transitional classes during schema generation, for example:
  - `PlatformReferenceGICSReferenceSchema`
  - `PlatformReferenceNAICSReferenceSchema`

Reason:

- This avoids class-name collision with the live bridge classes before cutover.

Validation:
- `./a_gr_venv/bin/python manage.py check`

Rollback:
- Revert only the future managed model addition.

### Step 3.3 Generate initial target schema

Command:

```zsh
./a_gr_venv/bin/python manage.py makemigrations platform_reference
```

Expected output file:

- rename generated migration to `platform_reference/migrations/0001_initial_reference_tables.py`

Expected operations inside:

- `CreateModel` for future GICS table
- `CreateModel` for future NAICS table
- matching indexes and unique constraints

Constraint parity to preserve:

- `GICSReference` unique on `(code, level)`
- equivalent indexes for:
  - `level, code`
  - `parent_code, level`
  - `is_active, level, code`
- equivalent indexes for NAICS:
  - `sector_code, code`
  - `is_active, code`

Draft name targets already aligned to live transitional code:

- `platform_re_level_gics_idx`
- `pr_gics_parent_level_idx`
- `platform_re_is_active_gics_idx`
- `platform_re_sector__naics_idx`
- `pr_naics_active_code_idx`

Validation:
- Review migration file before applying.

Rollback:
- Delete the generated migration file if not yet applied.

### Step 3.4 Create the data copy migration

Create file:

- `platform_reference/migrations/0002_copy_reference_data_from_platform_core.py`

Dependencies:

- `("platform_reference", "0001_initial_reference_tables")`
- `("platform_core", "0019_rename_platform_co_level_3b70f8_idx_platform_co_level_60ea83_idx_and_more")`

Required migration structure:

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

    # Safe only before the runtime bridge flips to platform_reference_* tables.
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

Copy requirements:

- Preserve `id`.
- Preserve timestamps.
- Preserve deterministic ordering by `id`.
- Use `update_or_create` for restart safety.
- Run copy outside one giant transaction (`atomic = False`).

Validation after apply:

- compare counts old vs new
- compare sample rows by `id`
- compare ordered `id` continuity for both datasets

Rollback:
- If runtime has not switched yet, delete copied rows from new tables and revert the migration.
- After runtime has switched, do not use simple migration reversal as the first rollback action.

### Step 3.5 Flip runtime bridge models to new tables

After data copy verification, change the live bridge classes in `platform_reference.models` from:

- `db_table = "platform_core_gicsreference"`
- `db_table = "platform_core_naicsreference"`

to:

- `db_table = "platform_reference_gicsreference"`
- `db_table = "platform_reference_naicsreference"`

Keep during this cut:

- `managed = False`

Reason:

- Runtime switches to the new physical tables without yet changing Django’s final schema-ownership behavior.

Validation commands:

```zsh
./a_gr_venv/bin/python manage.py check
./a_gr_venv/bin/python manage.py test platform_core.tests_reference_promotion_gate_command
./a_gr_venv/bin/python manage.py test platform_core.tests_mlas_executive_console
./a_gr_venv/bin/python manage.py reference_load_naics_snapshot
```

Optional controlled validations when licensed CSV is available:

```zsh
./a_gr_venv/bin/python manage.py reference_validate_gics --file /absolute/path/to/gics.csv
./a_gr_venv/bin/python manage.py reference_import_gics --file /absolute/path/to/gics.csv
```

Rollback:

- Revert the `db_table` flip back to `platform_core_*` tables.
- Do not drop any old tables before rollback completes.

### Step 3.6 Retire old platform_core tables

Create file:

- `platform_core/migrations/0020_drop_reference_tables_after_platform_reference_cutover.py`

Dependencies:

- `("platform_core", "0019_rename_platform_co_level_3b70f8_idx_platform_co_level_60ea83_idx_and_more")`
- `("platform_reference", "0002_copy_reference_data_from_platform_core")`

Expected operations:

- `DeleteModel` for `GICSReference`
- `DeleteModel` for `NAICSReference`

Important note:

- Only apply this migration after the runtime has already been running successfully on `platform_reference_*` tables.
- Treat this migration as a destructive boundary requiring explicit confirmation immediately before execution.
- Treat this step as an operator runbook checkpoint, not a routine continuation.

Validation after apply:

- rerun full focused validation set
- confirm no SQL references to `platform_core_gicsreference`
- confirm no SQL references to `platform_core_naicsreference`

Validation before apply should already include:

- matched old/new row counts
- ordered `id` continuity checks
- sampled row parity checks
- successful runtime writes through `platform_reference` commands

Rollback:

- If old tables are already dropped, rollback is no longer code-only.
- Treat this as the first materially destructive step and checkpoint before applying.
- Prefer a pre-drop backup checkpoint because post-drop recovery may require schema restoration, not just code reversion.

### Step 3.7 Remove bridge-state `managed = False`

Once old tables are retired and runtime is stable:

- change canonical `platform_reference` models to `managed = True`
- remove transitional schema-only class naming if used
- consolidate to the final canonical class names

Validation:

- `./a_gr_venv/bin/python manage.py check`
- focused tests
- inspect generated migrations before applying any follow-up schema diffs

Rollback:

- If no new schema migration was applied yet, revert the model metadata change.

## Exact Dependency Ordering

1. freeze bridge
2. add future managed schema classes
3. generate `platform_reference/migrations/0001_initial_reference_tables.py`
4. create and apply `platform_reference/migrations/0002_copy_reference_data_from_platform_core.py`
5. flip bridge `db_table` values to `platform_reference_*`
6. validate runtime on new tables
7. create and apply `platform_core/migrations/0020_drop_reference_tables_after_platform_reference_cutover.py`
8. remove `managed = False`

## Rollback Checkpoints

### Checkpoint A: before `0001_initial_reference_tables.py`

- Safe rollback: code-only.

### Checkpoint B: after `0001_initial_reference_tables.py`, before `0002_copy_reference_data_from_platform_core.py`

- Safe rollback: drop new empty tables by reverting migration.

### Checkpoint C: after data copy, before runtime flip

- Safe rollback: revert copy migration or truncate new tables if necessary.

### Checkpoint D: after runtime flip, before dropping old tables

- Safe rollback: restore `db_table` bindings to old tables.

### Checkpoint E: after dropping old tables

- Destructive boundary.
- Require explicit confirmation before execution.
- Prefer a schema/data backup checkpoint before applying.
- Do not combine this step with unrelated schema changes in the same execution window.

## Operator Checklist

- [ ] Confirm current bridge models still point at `platform_core_*` tables.
- [ ] Add future managed schema classes.
- [ ] Generate `0001_initial_reference_tables.py`.
- [ ] Review indexes and constraints for parity.
- [ ] Add `0002_copy_reference_data_from_platform_core.py`.
- [ ] Apply migrations in non-destructive order.
- [ ] Validate counts between old and new tables.
- [ ] Flip runtime bridge models to `platform_reference_*` tables.
- [ ] Re-run focused runtime validation.
- [ ] Confirm cutover stability.
- [ ] Create `0020_drop_reference_tables_after_platform_reference_cutover.py`.
- [ ] Obtain explicit confirmation before applying destructive cleanup.
- [ ] Remove `managed = False` after physical cutover is stable.

## Exact Draft Code

For the exact draft code for Step 3.2 and the exact draft contents of `0001_initial_reference_tables.py` and `0002_copy_reference_data_from_platform_core.py`, use:

- `docs/architecture/platform_reference_phase3_code_drafts.md`
