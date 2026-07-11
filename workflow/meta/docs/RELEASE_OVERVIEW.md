# Release Overview

## Purpose

This document defines deterministic release orchestration for the workflow platform.

## Release Inputs

- workflow/meta/registry.json
- workflow/meta/version.json
- workflow/meta/semantic_context.json
- workflow/meta/ai_hints.json
- workflow/meta/ai_navigation.json

## Release Commands

- python3 workflow/cli.py version
- python3 workflow/cli.py bump-version --part patch
- python3 workflow/cli.py release --bump patch
- python3 workflow/cli.py release-notes
- python3 workflow/release.py --bump patch
- python3 workflow/release_notes.py

## Release Safety Gates

Release fails when any gate fails:

1. semantic-drift gate
2. semantic-infer confidence gate
3. semantic-resolve conflict gate
4. validate-suite gate
5. visualize-all gate
6. sync-all gate
7. ai-export gate

## Release Outputs

- workflow/meta/version.json
- workflow/reports/release_notes.json
- workflow/meta/semantic_changelog.md
- workflow/meta/ai_hints.json
- workflow/meta/ai_navigation.json
- workflow/meta/semantic_context.json

## Governance Scope

Changes affecting MLAS tier, BTIF route, semantic intent, tag ontology, thresholds, or safety gates must be recorded in release notes and semantic changelog.
