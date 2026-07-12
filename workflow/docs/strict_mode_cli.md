# Strict Mode CLI Commands
Document ID: BTPE-CLI-STRICT-001
Version: v1.0
Status: Active

---

## 1. Overview

The Strict Mode workflow is fully integrated into the CLI through the WorkflowEngine.
This document describes the CLI commands that expose Strict Mode's metadata,
schema, semantic layers, and execution path.

These commands are available globally once the workflow engine initializes.

---

## 2. Commands Summary

### 2.1 workflows
Lists all registered workflows.

```bash
python3 workflow/cli.py workflows
```

Output example:

```text
Registered Workflows:
 - strict-mode
```

---

### 2.2 describe <workflow_id>
Displays manifest-level metadata for a workflow.

```bash
python3 workflow/cli.py describe strict-mode
```

Includes:
- Workflow name and ID
- Version and status
- Definition file
- Engine module
- Schema file
- Metadata file
- Propagation rules
- Documentation file
- Node list
- Semantic classification

---

### 2.3 introspect <workflow_id>
Performs deep inspection of workflow internals.

```bash
python3 workflow/cli.py introspect strict-mode
```

Displays:
- Full QPU schema
- Semantic metadata
- Propagation class
- Engine module internals

This command is intended for:
- semantic engine developers
- workflow designers
- debugging and validation
- VS Code AI indexing

---

## 3. Execution Example

Strict Mode can be executed through the CLI using:

```bash
python3 workflow/cli.py strict-mode \
--name "QPU Strict Mode" \
--inverse-pairs "red:green" "blue:yellow" \
--relay-segment "red blue yellow green" \
--srl-values 4 16 64 256 \
--tenses past present-past present-future future \
--btif-subjects Math Language Arts Science \
--semantic-tags strict qpu relay inverse temporal
```

Output includes:
- schema-validated QPU
- semantic block
- strict_mode_enriched
- btpe_layer

---

## 4. Integration Notes

These commands rely on:
- WorkflowEngine
- WorkflowEngineBootstrap
- WorkflowRegistry
- Strict Mode manifest
- Strict Mode index entry
- Strict Mode engine module
- Strict Mode schema
- Strict Mode metadata
- Strict Mode propagation rules

All components are auto-discovered and registry-loaded at engine initialization.

---

## 5. Status

Strict Mode CLI commands are fully operational and integrated with:
- workflow engine
- registry
- autodiscovery
- semantic metadata
- schema validation
- documentation layer
