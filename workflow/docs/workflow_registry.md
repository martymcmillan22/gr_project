# Workflow Registry Documentation
Document ID: BTPE-REGISTRY-001
Version: v1.0
Status: Active

---

## 1. Overview

The Workflow Registry is the global catalog of all workflows available in the
BaseTrue Pattern Engine (BTPE). It is responsible for:

- storing workflow manifest and index entries
- enabling workflow lookup and enumeration
- supporting autodiscovery
- providing workflow metadata to the engine and CLI
- ensuring Strict Mode and future workflows are globally visible

The registry is initialized automatically during engine bootstrap.

---

## 2. Registry Architecture

The registry is defined in:
workflow/registry/workflow_registry.py

It contains:

- an internal _registry dictionary
- a register() method for adding workflows
- a _bootstrap() method for autodiscovery
- lookup and enumeration helpers

Strict Mode is registered automatically through the autodiscovery system.

---

## 3. Autodiscovery Integration

Autodiscovery is handled by:
workflow/autodiscovery/strict_mode_loader.py

During registry bootstrap:
load_strict_mode(self)

is executed, which registers Strict Mode using:

- manifest
- index entry
- semantic metadata
- node list
- documentation paths

This ensures Strict Mode is available without manual imports.

---

## 4. Registry Methods

### 4.1 register(workflow_id, manifest, index_entry)
Adds a workflow to the registry.

### 4.2 list_workflows()
Returns all registered workflow IDs.

Example output:
["strict-mode"]

### 4.3 get(workflow_id)
Returns the manifest + index entry for a workflow.

Example:
registry.get("strict-mode")

returns a populated dictionary containing:

- definition
- engine module
- schema
- metadata
- propagation rules
- documentation
- nodes
- semantic classification

---

## 5. Registry + Engine Integration

The registry is consumed by the main engine:
workflow/engine/workflow_engine.py

The engine uses the registry to:

- list workflows
- describe workflows
- introspect workflows
- execute workflows
- dynamically load workflow engine modules

Strict Mode is fully integrated into this pipeline.

---

## 6. Registry + CLI Integration

The CLI uses the registry through the WorkflowEngine to power:

- workflows
- describe <workflow_id>
- introspect <workflow_id>
- strict-mode execution

All of these commands rely on registry-backed workflow discovery.

---

## 7. Strict Mode Registry Entry

Strict Mode's registry entry includes:

- workflow ID
- manifest
- index entry
- semantic metadata
- node list
- documentation paths

This entry is created automatically during bootstrap.

---

## 8. Status

The Workflow Registry is fully operational and integrated with:

- WorkflowEngine
- Autodiscovery
- CLI workflow commands
- Semantic metadata
- Schema validation
- Documentation layer
