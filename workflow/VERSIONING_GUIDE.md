# Versioning Guide

## Canonical Version File

Use workflow/version.json as the single source of truth.

Tracked layer versions:

- workflow_engine_version
- semantic_engine_version
- sync_layer_version
- visualization_layer_version
- cli_version
- ai_native_layer_version

## Semantic Versioning Rules

1. Major:
- breaking semantic rules
- registry schema changes

2. Minor:
- new CLI commands
- new semantic rules
- new sync outputs

3. Patch:
- bug fixes
- drift rule updates
- inference tuning

## CLI Usage

- python3 workflow/cli.py version
- python3 workflow/cli.py bump-version --part major|minor|patch

## Release Integration

The release pipeline updates version.json and writes:

- release_notes.json
- semantic_changelog.md

Version bump result includes previous and current versions per layer.
