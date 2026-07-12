# Strict Mode Workflow Definition Documentation
Document ID: BTPE-WF-DEF-STRICT-001
Version: v1.0
Status: Active

---

## 1. Overview

The Strict Mode workflow definition is stored in:
workflow/definitions/strict_mode.workflow.json

This JSON file provides the canonical declarative structure for the Strict Mode
workflow. It is consumed by:

- WorkflowEngine
- WorkflowRegistry
- CLI execution
- semantic metadata propagation
- schema validation
- VS Code AI indexing

The definition file is the source of truth for workflow structure.

---

## 2. Definition Structure

The Strict Mode workflow definition contains the following top-level fields:

- workflow_id
- name
- version
- nodes
- roles
- semantic_tags
- btif_subjects
- classification
- engine_module
- schema_file
- metadata_file
- propagation_file

These fields are used by the engine to assemble the full execution pipeline.

---

## 3. Node Definitions

Strict Mode contains four nodes:

1. inverse_pair_node
   Role: inverse-validation
   Validates two complete inverse pairs.

2. relay_alignment_node
   Role: relay-validation
   Ensures colors form a contiguous Linear Relay segment.

3. srl_node
   Role: srl-scaling
   Validates SRL x4 growth across repositories.

4. temporal_mapping_node
   Role: temporal-mapping
   Maps relay segment to Past -> Present-Past -> Present-Future -> Future.

These nodes appear in the definition JSON under the "nodes" array.

---

## 4. Semantic Metadata

The definition includes semantic metadata fields:

- semantic_intent: QPU-Strict-Validation
- semantic_tags: strict, qpu, relay, inverse, temporal, srl
- btif_subjects: Math, Language, Arts, Science

These fields are used by:

- semantic engines
- metadata propagation
- documentation generators
- VS Code AI indexing

---

## 5. Classification Block

The "classification" block defines the workflow's identity:

"type": "workflow",
"tier": "strict",
"category": "qpu-validation",
"engine": "BTPE"

This classification is used by:

- BTPE semantic engine
- workflow introspection
- CLI describe/introspect commands
- documentation generators

---

## 6. Engine Integration

The definition file points to the engine module:
workflow/engine/strict_mode_engine.py

The WorkflowEngine dynamically imports this module using the path provided in the
definition JSON.

---

## 7. Schema Integration

The definition file references the QPU schema:
workflow/schema/strict_mode_qpu_schema.py

This schema is used to validate workflow output during execution.

---

## 8. Metadata & Propagation Integration

The definition file includes:

- metadata_file: strict_mode_metadata.py
- propagation_file: strict_mode_propagation.py

These files enrich workflow output with semantic layers.

---

## 9. Status

The Strict Mode workflow definition is fully integrated with:

- WorkflowEngine
- WorkflowRegistry
- Autodiscovery
- CLI workflow commands
- Semantic metadata
- Schema validation
- Documentation layer
