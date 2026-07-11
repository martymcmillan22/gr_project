# Release Overview

## Purpose

This document defines deterministic release orchestration for the workflow platform.

## Release Inputs

- workflow/registry.json
- workflow/version.json
- workflow/semantic_context.json
- workflow/ai_hints.json
- workflow/ai_navigation.json

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

- workflow/version.json
- workflow/release_notes.json
- workflow/semantic_changelog.md
- workflow/ai_hints.json
- workflow/ai_navigation.json
- workflow/semantic_context.json

## Governance Scope

Changes affecting MLAS tier, BTIF route, semantic intent, tag ontology, thresholds, or safety gates must be recorded in release notes and semantic changelog.
