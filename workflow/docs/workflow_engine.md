# Workflow Engine Documentation
Document ID: BTPE-ENGINE-001
Version: v1.0
Status: Active

---

## 1. Overview

The Workflow Engine is the central execution and discovery system for all
workflows in the BaseTrue Pattern Engine (BTPE). It provides:

- automatic workflow discovery
- global workflow registry
- dynamic engine loading
- schema-validated execution
- semantic metadata propagation
- CLI integration

Strict Mode is fully integrated into this engine.

---

## 2. Engine Architecture

The engine is composed of four primary layers:

1. Bootstrap Layer
File: workflow/engine/bootstrap.py
- Initializes the workflow registry
- Triggers autodiscovery
- Loads Strict Mode automatically

2. Registry Layer
File: workflow/registry/workflow_registry.py
- Stores all workflow entries
- Provides lookup and enumeration
- Registers workflows via autodiscovery

3. Autodiscovery Layer
File: workflow/autodiscovery/strict_mode_loader.py
- Automatically registers Strict Mode
- Ensures Strict Mode is available without manual imports

4. Execution Layer
File: workflow/engine/workflow_engine.py
- Dynamically loads workflow engine modules
- Executes workflows using manifest definitions
- Returns schema-validated, semantically enriched output

---

## 3. Engine Initialization

Engine initialization occurs through:

```python
WorkflowEngine()
```

This triggers:

1. Bootstrap
2. Registry creation
3. Autodiscovery
4. Strict Mode registration

After initialization, the engine can:

- list workflows
- describe workflows
- introspect workflows
- execute workflows

---

## 4. Workflow Execution

Workflows are executed through:

```python
engine.run(workflow_id, payload)
```

Execution steps:

1. Lookup workflow in registry
2. Load manifest
3. Dynamically import engine module
4. Instantiate workflow engine class
5. Run workflow with provided payload
6. Validate output against schema
7. Attach semantic metadata
8. Propagate semantic layers

Strict Mode produces:

- strict_mode_enriched
- btpe_layer
- schema-validated QPU

---

## 5. Dynamic Engine Loading

The engine dynamically imports workflow modules using:

```python
_import_engine(engine_path)
```

Supports:

- script-mode imports
- package-mode imports

Fallback engine class detection ensures compatibility with:

- StrictModeEngine
- future workflow engines

---

## 6. Registry Integration

The registry stores:

- manifest
- index entry
- semantic metadata
- node list
- documentation paths

Strict Mode is registered automatically via:

```python
load_strict_mode(self)
```

---

## 7. CLI Integration

The engine powers the following CLI commands:

- workflows
- describe <workflow_id>
- introspect <workflow_id>
- strict-mode (execution)

All commands use the central WorkflowEngine instance.

---

## 8. Strict Mode Integration Summary

Strict Mode is integrated at every layer:

- Manifest: strict_mode_manifest.py
- Index: workflow_index.py
- Autodiscovery: strict_mode_loader.py
- Registry: workflow_registry.py
- Engine: strict_mode_engine.py
- Schema: strict_mode_qpu_schema.py
- Metadata: strict_mode_metadata.py
- Propagation: strict_mode_propagation.py
- Docs: strict_mode.md, strict_mode_cli.md

Strict Mode is now a first-class workflow type.

---

## 9. Status

The Workflow Engine is fully operational and integrated with:

- registry
- autodiscovery
- CLI
- semantic metadata
- schema validation
- documentation layer
