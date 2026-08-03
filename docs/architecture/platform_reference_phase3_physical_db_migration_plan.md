# Platform Reference Phase 3 Physical DB Migration Plan

## Takeaway

The Python-layer ownership transfer for `GICSReference` and `NAICSReference` is complete.

That means the next phase is no longer about imports, admin, commands, or services. It is about moving the physical database tables so the schema catches up to the application layer.

This plan defines the deterministic sequence for that transition.

## Preconditions

Phase 3 starts only because the following are already true:

- Python ownership is complete.
- Runtime imports are unified under `platform_reference.models`.
- Admin ownership is unified under `platform_reference`.
- Reference commands and services are unified under `platform_reference`.
- `managed = False` mapped bridge models are stable.
- The reference surface has focused validation coverage.

## Safety Rules

- Do not mutate the current live tables until the future schema exists.
- Do not switch runtime reads and writes to new tables until data copy is verified.
- Do not drop old monolith tables until post-copy validation is green.
- Keep each step reversible until the old tables are explicitly retired.

## Deterministic Timeline

### 3.1 Freeze the current mapped bridge models

Keep the current `platform_reference.models` bridge exactly as-is:

```python
class GICSReference(models.Model):
    class Meta:
        managed = False
        db_table = "platform_core_gicsreference"
```

And likewise for `NAICSReference`.

Purpose:
- Preserve a stable runtime bridge to the old physical tables while the new schema is prepared.

Result:
- No runtime or schema change yet.

### 3.2 Introduce future canonical managed models in platform_reference

Create new managed model definitions that target future `platform_reference_*` tables.

Example target state:

```python
class GICSReference(models.Model):
    class Meta:
        managed = True
        db_table = "platform_reference_gicsreference"
```

Important constraint:
- These future managed models should exist only to generate the new schema.
- They must not replace the bridge models in the runtime path yet.

Purpose:
- Let Django generate the future canonical schema without changing the current runtime bridge.

Result:
- Future schema shape is defined in code.

### 3.3 Generate initial platform_reference schema migrations

Run:

- `makemigrations platform_reference`

Expected output:

- `0001_initial.py`
- New managed table definitions for `platform_reference_gicsreference`
- New managed table definitions for `platform_reference_naicsreference`

Purpose:
- Establish future empty canonical tables.

Result:
- Schema migrations exist, but no data has moved yet.

### 3.4 Create a data migration from old tables to new tables

Add a migration using `RunPython(copy_reference_data)`.

The copy function must:

- Read from old monolith tables.
- Write to new `platform_reference_*` tables.
- Preserve primary keys where feasible.
- Preserve row ordering deterministically.
- Preserve any future relational assumptions.
- Be idempotent or safely restartable when possible.

Purpose:
- Populate the future canonical tables with the current reference dataset.

Result:
- New tables are physically populated.

### 3.5 Flip the bridge models to point at the new tables

Once copy validation is complete, update the bridge model table bindings:

```python
class GICSReference(models.Model):
    class Meta:
        managed = False
        db_table = "platform_reference_gicsreference"
```

And likewise for `NAICSReference`.

At that moment:

- Runtime reads use new physical tables.
- Runtime writes use new physical tables.
- Admin uses new physical tables.
- Commands use new physical tables.
- Tests use new physical tables.

Purpose:
- Transfer physical runtime ownership from monolith tables to reference-owned tables.

Result:
- The application is live on the new physical tables.

### 3.6 Retire old monolith tables

After the runtime is stable on the new tables:

- Add cleanup migration(s) in `platform_core`.
- Remove legacy reference table definitions from schema ownership.
- Drop old physical tables only after validation gates are green.

Purpose:
- Remove leftover monolith schema once it is no longer used.

Result:
- The old physical tables are retired.

### 3.7 Remove the bridge-state `managed = False`

After the new tables are canonical and the old tables are gone:

- Set the canonical `platform_reference` models to `managed = True`.
- Let Django fully own the schema from that point forward.

Purpose:
- End the transitional bridge state.

Result:
- `platform_reference` becomes the full schema owner at both Python and database layers.

## Compact Timeline

| Step | Action | Result |
| --- | --- | --- |
| 3.1 | Freeze mapped bridge models | Stable runtime bridge |
| 3.2 | Add future canonical managed models | Future schema defined |
| 3.3 | Generate platform_reference migrations | New empty tables |
| 3.4 | Copy data old -> new | New tables populated |
| 3.5 | Flip bridge models to new tables | Runtime moves to new physical tables |
| 3.6 | Drop old monolith tables | Legacy schema retired |
| 3.7 | Remove `managed = False` | platform_reference fully canonical |

## Validation Gates Per Step

Run at minimum after each executable cut:

- `manage.py check`
- `platform_core.tests_reference_promotion_gate_command`
- `platform_core.tests_mlas_executive_console`

And after the physical switch in 3.5 also run:

- `manage.py reference_load_naics_snapshot`
- `manage.py reference_import_gics --file ...` against a controlled input when available
- `manage.py reference_validate_gics --file ...` against a controlled input when available

## Scope Expansion After GICS and NAICS

Once this pattern is proven for `GICSReference` and `NAICSReference`, repeat the same deterministic sequence for later reference datasets such as:

- MLAS
- CCPP
- DCHD

## Immediate Next Step

The next safe action is Phase 3.1 only:

- Freeze the current mapped bridge models as the stable baseline.
- Do not generate migrations or mutate schema until you explicitly choose to begin Phase 3 execution.

## Execution Checklist

For the exact migration filenames, app labels, `RunPython` copy stubs, dependency ordering, and rollback checkpoints, use:

- `docs/architecture/platform_reference_phase3_execution_checklist.md`

For the exact draft model code and exact draft migration bodies before any `makemigrations` run, use:

- `docs/architecture/platform_reference_phase3_code_drafts.md`
