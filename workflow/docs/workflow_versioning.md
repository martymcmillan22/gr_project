# Workflow Versioning & Changelog Specification
Document ID: BTPE-VERSIONING-001
Version: v1.0
Status: Active

---

## 1. Overview

This document defines the versioning rules and changelog structure for workflows
in the BaseTrue Pattern Engine (BTPE). It ensures consistent lifecycle
management across:

- workflow definitions  
- engine modules  
- schema files  
- metadata files  
- propagation rules  
- documentation  
- packaging manifests  

Strict Mode is the reference implementation for these rules.

---

## 2. Versioning Model

BTPE workflows use a deterministic semantic versioning model:

MAJOR.MINOR.PATCH

### 2.1 MAJOR Version
Increment when:

- workflow structure changes  
- node list changes  
- semantic intent changes  
- classification changes  
- engine contract changes  
- schema structure changes  

### 2.2 MINOR Version
Increment when:

- new metadata fields are added  
- new documentation is added  
- new CLI commands are added  
- new semantic tags are added  
- new propagation rules are added  
- non-breaking engine improvements occur  

### 2.3 PATCH Version
Increment when:

- bug fixes occur  
- documentation corrections occur  
- schema refinements occur  
- metadata corrections occur  
- propagation tweaks occur  

---

## 3. Changelog Structure

Each workflow maintains a changelog file:

workflow/docs/changelog/<workflow_id>.md

Strict Mode uses:

workflow/docs/changelog/strict_mode.md

### 3.1 Changelog Format

# Changelog — <Workflow Name>

## Version X.Y.Z — YYYY-MM-DD

### Added

- ...

### Changed

- ...

### Fixed

- ...

### Removed

- ...

This format is stable, machine-parseable, and human-readable.

---

## 4. Version Sources

Workflow version is declared in:

- `strict_mode.workflow.json`  
- `strict_mode_manifest.py`  
- `workflow_package_manifest.py`  
- documentation pages  
- CLI describe/introspect output  

All sources must match.

---

## 5. Version Enforcement

The WorkflowEngine enforces version consistency by:

- loading manifest version  
- loading index version  
- loading packaging manifest version  
- exposing version through CLI commands  
- exposing version through introspection API  

If versions mismatch, the engine may:

- warn  
- reject execution  
- require upgrade  

---

## 6. Version Compatibility

Workflows declare compatibility with:

- BTPE version  
- workflow engine version  
- schema version  

Compatibility is defined in the packaging manifest (FILE 28).

---

## 7. Strict Mode Versioning Example

Strict Mode currently uses:

Version: 1.0.0
Status: active

### 7.1 MAJOR Change Examples
- Adding a fifth node  
- Changing semantic intent  
- Changing classification  
- Changing QPU schema structure  

### 7.2 MINOR Change Examples
- Adding new semantic tags  
- Adding new documentation pages  
- Adding new CLI commands  

### 7.3 PATCH Change Examples
- Fixing metadata typos  
- Adjusting propagation rules  
- Improving engine error messages  

---

## 8. Status

The versioning and changelog system is fully integrated with:

- WorkflowEngine  
- WorkflowRegistry  
- Autodiscovery  
- CLI workflow commands  
- Packaging manifest  
- Documentation layer  
