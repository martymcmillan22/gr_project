# Platform Core Split: Phase 2a Reference Extraction Map

## Scope

This document defines the first deterministic extraction wave from `platform_core` into `platform_reference`.

## Rules

- Keep runtime behavior unchanged.
- Use compatibility shims where imports are widely used.
- Move stateless service logic first.
- Move models and migrations in later waves.

## Wave Plan

| Wave | Target | Source | Destination | Strategy | Risk |
| --- | --- | --- | --- | --- | --- |
| 2a.1 | Reference status service | `platform_core/reference_sync.py` | `platform_reference/services/reference_sync.py` | Copy logic, switch selected imports, keep shim in source | Low |
| 2a.2 | Promotion gate command imports | `platform_core/management/commands/check_reference_promotion_gate.py` | consume from `platform_reference.services.reference_sync` | Direct import switch | Low |
| 2a.3 | Executive reference status imports | `platform_core/views.py` | consume from `platform_reference.services.reference_sync` | Direct import switch | Low |
| 2b | GICS/NAICS management commands | `platform_core/management/commands/import_gics_reference.py`, `validate_gics_reference.py` | `platform_reference/services/*` then `platform_reference/management/commands/*` | Extract implementation to reference services, keep core command wrappers, then transfer command ownership | Medium |
| 2c | Reference admin surface | `platform_core/admin.py` reference sections | `platform_reference/admin.py` | Split registration by model ownership | Medium |
| 2d | Reference models | `platform_core/models.py` (`GICSReference`, `NAICSReference`) | `platform_reference/models.py` | Multi-step migrations and foreign-key remap | High |

## Completed In This Change

- Implemented wave `2a.1` with compatibility shim.
- Implemented wave `2a.2` by switching command import path.
- Implemented wave `2a.3` by switching view import path.
- Implemented wave `2b.1` by extracting `validate_gics_reference` logic to `platform_reference/services/reference_validation.py` and keeping a thin wrapper command in `platform_core`.
- Implemented wave `2b.2` by extracting `import_gics_reference` logic to `platform_reference/services/reference_import.py` and keeping a thin wrapper command in `platform_core`.
- Implemented wave `2b.3` by extracting `load_naics_reference_snapshot` logic to `platform_reference/services/reference_import.py` and keeping a thin wrapper command in `platform_core`.
- Implemented wave `2b.4` by adding owned platform-reference command entrypoints: `reference_validate_gics`, `reference_import_gics`, and `reference_load_naics_snapshot` under `platform_reference/management/commands`.
- Implemented wave `2c` by moving NAICS/GICS admin registration ownership to `platform_reference/admin.py` while models remain in `platform_core`.
- Implemented wave `2d` planning artifact at `docs/architecture/platform_core_split_phase2d_model_migration_plan.md` with dependency inventory, stepwise migration sequence, and rollback gates.
- Implemented wave `2d.1` by introducing `GICSReference` and `NAICSReference` model classes in `platform_reference/models.py` mapped to existing `platform_core_*` tables with `managed = False`.
- Implemented wave `2d.2` foundation by switching `platform_reference` services/admin imports to `platform_reference.models` while keeping `platform_core` model definitions for compatibility.
- Implemented wave `2d.3` by adding dual admin namespace fallback in `platform_core/views.py` and making executive console tests namespace-tolerant for NAICS/GICS admin links.
- Implemented the first `2d.4` runtime import transition slice by switching `platform_core/views.py` to read `GICSReference` and `NAICSReference` from `platform_reference.models`; remaining direct `platform_core.models` imports are now test-only.
- Completed the next `2d.4` cleanup slice by switching the remaining test imports to `platform_reference.models`; there are now no direct `GICSReference` or `NAICSReference` imports from `platform_core.models`.
- Implemented `2d.5` by replacing `platform_core.models` reference model class bodies with compatibility aliases to `platform_reference.models`, leaving database tables unchanged.
- Implemented `2d.6` by retiring the `platform_core.models` compatibility aliases entirely; `platform_reference.models` is now the sole Python import owner for `GICSReference` and `NAICSReference`.
- Added the physical schema migration plan for the next stage at `docs/architecture/platform_reference_phase3_physical_db_migration_plan.md`.
- Added the Phase 3 execution checklist at `docs/architecture/platform_reference_phase3_execution_checklist.md`.
- Promoted Phase `3.2` transitional managed schema classes into real code in `platform_reference/models.py` without running `makemigrations` or mutating schema.
- Began Phase `3.3` by generating the real migration artifact `platform_reference/migrations/0001_initial_reference_tables.py`; it has not been applied, so no database schema mutation has occurred.
- Materialized the real data-copy migration artifact `platform_reference/migrations/0002_copy_reference_data_from_platform_core.py`; it has not been applied, so no data mutation has occurred.
- Crossed the first apply boundary by applying `platform_reference.0001_initial_reference_tables` and validating migration state, checks, schema objects, and focused tests.
- Crossed the second apply boundary by applying `platform_reference.0002_copy_reference_data_from_platform_core` and validating migration state, checks, parity counts, and focused tests.
- Completed strict field-level parity audit between `platform_core_*reference` and `platform_reference_*reference` tables with zero mismatches on shared mapped columns for both GICS and NAICS.
- Implemented post-copy write routing in `platform_reference/services/reference_import.py` so command-driven GICS/NAICS upserts target `platform_reference_*` schema models instead of legacy `platform_core_*` bridge tables.
- Applied and validated non-destructive deprecation migration `platform_core/migrations/0020_reference_tables_deprecation_state_marker.py` using state-only operations (`SeparateDatabaseAndState`) with no database mutations (`sqlmigrate` no-op).
- Added legacy-drop migration draft `platform_core/migrations/0021_drop_legacy_reference_tables_draft.py` with explicit forward DROP SQL and reverse CREATE SQL/index rebuild statements; migration is generated and reviewed via `sqlmigrate` but remains unapplied.

## Verification Checklist

- `manage.py check` passes.
- `platform_core.tests_reference_promotion_gate_command` passes.
- `platform_core.tests_mlas_executive_console` passes.

## Next Deterministic Step

Phase `2d` Python-layer ownership transfer is complete, the Phase `3.3`/`3.4` apply boundaries are complete and validated, the `platform_core` state-only deprecation marker migration (`0020_reference_tables_deprecation_state_marker`) is applied, and the legacy-drop draft migration (`0021_drop_legacy_reference_tables_draft`) is generated and reviewed but not applied. The next safe step is an explicit go/no-go decision before any destructive apply boundary.
