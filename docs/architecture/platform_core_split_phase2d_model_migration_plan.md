# Platform Core Split: Phase 2d Model Migration Plan

## Objective

Move model ownership for `GICSReference` and `NAICSReference` from `platform_core` to `platform_reference` with deterministic, append-only migration steps and no data loss.

## Current Dependency Inventory

### Model definitions (current owner)

- `platform_core/models.py`
  - `NAICSReference`
  - `GICSReference`

### Migration history (current owner)

- `platform_core/migrations/0018_reference_datasets.py`
  - creates both reference tables and constraints/indexes
- `platform_core/migrations/0019_rename_platform_co_level_3b70f8_idx_platform_co_level_60ea83_idx_and_more.py`
  - renames related indexes

### Runtime imports and services

- `platform_reference/services/reference_sync.py`
- `platform_reference/services/reference_validation.py`
- `platform_reference/services/reference_import.py`
- `platform_core/views.py`
- `platform_core/management/commands/validate_gics_reference.py`
- `platform_core/management/commands/import_gics_reference.py`
- `platform_core/management/commands/load_naics_reference_snapshot.py`
- `platform_reference/management/commands/reference_validate_gics.py`
- `platform_reference/management/commands/reference_import_gics.py`
- `platform_reference/management/commands/reference_load_naics_snapshot.py`

### Admin dependencies

- `platform_reference/admin.py` currently registers `platform_core` model classes.
- `platform_core/views.py` reverses explicit admin URLs:
  - `admin:platform_core_naicsreference_changelist`
  - `admin:platform_core_gicsreference_changelist`

### Test dependencies

- `platform_core/tests_mlas_executive_console.py`
  - imports models from `platform_core.models`
  - asserts admin links under `/admin/platform_core/...`
- `platform_core/tests_reference_promotion_gate_command.py`
  - imports `GICSReference` from `platform_core.models`

### Relational risk check

- No foreign keys targeting `GICSReference` or `NAICSReference` were found.
- Most dependencies are import paths, admin URL names, and command/service callers.

## Safety Rules For 2d

- Do not drop or rename existing database tables in initial 2d execution.
- Separate Python ownership changes from physical database operations.
- Keep compatibility aliases until all imports and tests are switched.
- Verify after each micro-step with:
  - `manage.py check`
  - `platform_core.tests_reference_promotion_gate_command`
  - `platform_core.tests_mlas_executive_console`

## Proposed Deterministic Sequence

### 2d.1 Introduce reference-owned model classes without DB mutation

1. Add `GICSReference` and `NAICSReference` classes to `platform_reference/models.py` mapped to existing tables via explicit `db_table`.
2. Keep `platform_core` models present as compatibility aliases.
3. Do not remove old models in this step.

Expected outcome:
- Both apps can import reference models while still hitting the same physical rows.

### 2d.2 Add import compatibility layer

1. Create/extend a shared import surface in `platform_reference` (for example, `platform_reference/models.py` exports canonical classes).
2. Update `platform_reference/services/*` to import from `platform_reference.models`.
3. Keep `platform_core` command wrappers unchanged.

Expected outcome:
- Reference app runtime paths no longer depend on `platform_core.models` for these two model classes.

### 2d.3 Admin URL compatibility prep

1. Update `platform_core/views.py` admin link resolution to support both admin namespaces during transition.
2. Update tests to accept compatibility behavior or use namespace-agnostic assertions.

Expected outcome:
- Admin link generation remains stable even if registration namespace flips.

### 2d.4 Transfer admin registration to canonical reference model classes

1. Keep admin classes in `platform_reference/admin.py`.
2. Register using the new `platform_reference.models` classes.

Expected outcome:
- Admin ownership and model ownership align in the same app.

### 2d.5 Switch remaining call sites

1. Migrate direct imports in views/tests/commands from `platform_core.models` to `platform_reference.models` for these two models.
2. Keep compatibility aliases in `platform_core.models` until all references are switched.

Expected outcome:
- Runtime and test surfaces consistently use reference-owned model paths.

### 2d.6 Remove compatibility aliases (final cleanup)

1. Remove `GICSReference` and `NAICSReference` definitions/aliases from `platform_core.models` only after all callers are migrated.
2. Add a final migration/state alignment step if needed.

Expected outcome:
- Ownership fully transferred.

## Rollback Strategy

- If any step fails, revert only the latest step and keep previous compatibility paths.
- Because no table drop/rename is included in early 2d, rollback is low risk and code-only.

## Exit Criteria

- All runtime imports for `GICSReference` and `NAICSReference` originate from `platform_reference.models`.
- Admin links render correctly and tests pass.
- `manage.py check` passes.
- Targeted tests pass.
- No data migration errors and no table loss.
