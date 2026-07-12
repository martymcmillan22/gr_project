# Autodiscovery System Documentation
Document ID: BTPE-AUTODISCOVERY-001
Version: v1.0
Status: Active

---

## 1. Overview

The autodiscovery system is responsible for automatically registering workflows
into the global Workflow Registry during engine bootstrap. This ensures that
workflows such as Strict Mode are available without requiring manual imports or
explicit registration calls.

Autodiscovery is triggered during registry initialization and is part of the
core workflow engine architecture.

---

## 2. Autodiscovery Architecture

Autodiscovery consists of three components:

1. Loader Modules
Example: workflow/autodiscovery/strict_mode_loader.py
These modules contain functions that register workflows into the registry.

2. Registry Bootstrap
File: workflow/registry/workflow_registry.py
The _bootstrap() method calls all autodiscovery loaders.

3. Engine Bootstrap
File: workflow/engine/bootstrap.py
Initializes the registry, which triggers autodiscovery.

---

## 3. Strict Mode Autodiscovery

Strict Mode is registered automatically through:
load_strict_mode(self)

This function:

- registers the workflow ID
- attaches the manifest
- attaches the index entry
- exposes semantic metadata
- exposes documentation paths
- exposes node list
- ensures Strict Mode is globally discoverable

Strict Mode becomes available immediately after engine initialization.

---

## 4. Loader Module Structure

Autodiscovery loader modules follow a consistent pattern:

def load_<workflow>(registry):
registry.register(
workflow_id=...,
manifest=...,
index_entry=...
)
return True

This pattern ensures:

- deterministic registration
- compatibility with future workflows
- clean integration with registry bootstrap

---

## 5. Registry Integration

The registry calls autodiscovery during initialization:

def _bootstrap(self):
load_strict_mode(self)

This guarantees:

- Strict Mode is always registered
- CLI commands can discover workflows
- WorkflowEngine can execute workflows
- VS Code AI can index workflows
- BTPE semantic engine can introspect workflows

---

## 6. Engine Integration

The WorkflowEngine initializes the registry through:

self.bootstrap = WorkflowEngineBootstrap()
self.registry = self.bootstrap.get_registry()

This ensures autodiscovery is triggered before any workflow operations occur.

---

## 7. CLI Integration

Autodiscovery enables the following CLI commands:

- workflows
- describe strict-mode
- introspect strict-mode
- strict-mode execution

All of these rely on autodiscovery to populate the registry.

---

## 8. Status

The autodiscovery system is fully operational and integrated with:

- WorkflowRegistry
- WorkflowEngine
- CLI workflow commands
- Manifest + Index layers
- Semantic metadata
- Documentation layer
