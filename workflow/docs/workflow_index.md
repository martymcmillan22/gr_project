# Workflow Index Documentation
Document ID: BTPE-WF-INDEX-001
Version: v1.0
Status: Active

---

## 1. Overview

The Workflow Index is the global registry of all workflow types available in the
BaseTrue Pattern Engine (BTPE) ecosystem. It is populated automatically through
the workflow registry and autodiscovery system.

This document provides a human-readable and AI-indexable reference for all
registered workflows, including their manifest, schema, metadata, and
documentation paths.

---

## 2. Registered Workflows

The following workflows are currently registered and discoverable:

- strict-mode
- creator-workflow
- genre-classifier

This list is generated from:
workflow/index/workflow_index.py

---

## 3. Workflow: strict-mode

### 3.1 Identity
- ID: strict-mode
- Name: QPU Strict Mode
- Version: 1.0
- Status: active

### 3.2 Definition and Engine
- Definition File: workflow/definitions/strict_mode.workflow.json
- Engine Module: workflow/engine/strict_mode_engine.py

### 3.3 Schema and Metadata
- Schema: strict_mode_qpu_schema.py
- Metadata: strict_mode_metadata.py
- Propagation Rules: strict_mode_propagation.py

### 3.4 Documentation
- Workflow Docs: strict_mode.md
- CLI Docs: strict_mode_cli.md

### 3.5 Nodes
- inverse_pair_node.py
- relay_alignment_node.py
- srl_node.py
- temporal_mapping_node.py

### 3.6 Semantic Classification
- Intent: QPU-Strict-Validation
- Tags: strict, qpu, relay, inverse, temporal, srl
- BTIF Subjects: Math, Language, Arts, Science
- Category: qpu-validation
- Engine: BTPE

---

## 4. Workflow: creator-workflow

### 4.1 Identity
- ID: creator-workflow
- Name: Narrative Creator Workflow
- Version: 1.0
- Status: active

### 4.2 Definition and Engine
- Definition File: workflow/definitions/creator_workflow.workflow.json
- Engine Module: workflow/engine/creator_workflow_engine.py

### 4.3 Schema and Metadata
- Schema: creator_workflow_qpu_schema.py
- Metadata: creator_workflow_metadata.py
- Propagation Rules: creator_workflow_propagation.py

### 4.4 Documentation
- Workflow Docs: creator_workflow.md
- CLI Docs: creator_workflow_cli.md

### 4.5 Nodes
- creator_seed_node.py
- creator_arc_node.py
- creator_outline_node.py
- creator_render_node.py

### 4.6 Semantic Classification
- Intent: QPU-Creator-Output
- Tags: creator, narrative, transformer, output, workflow
- BTIF Subjects: Math, Language, Arts, Science
- Category: narrative-generation
- Engine: BTPE

---

## 5. Workflow: genre-classifier

### 5.1 Identity
- ID: genre-classifier
- Name: Genre Classifier Workflow
- Version: 1.0.0
- Status: active

### 5.2 Definition and Engine
- Definition File: workflow/definitions/genre_classifier.workflow.json
- Engine Module: workflow/engine/genre_classifier_engine.py

### 5.3 Schema and Metadata
- Schema: genre_classifier_schema.py
- Metadata: genre_classifier_metadata.py
- Propagation Rules: genre_classifier_propagation.py

### 5.4 Documentation
- Workflow Docs: genre_classifier.md
- CLI Docs: genre_classifier_cli.md
- Definition Docs: genre_classifier_definition.md

### 5.5 Nodes
- signal_extraction_node.py
- genre_rule_engine_node.py
- classification_output_node.py

### 5.6 Semantic Classification
- Intent: Genre-Classification
- Tags: genre, classification, semantic, qpu, structure, analysis
- BTIF Subjects: Language, Arts, Science, Math
- Category: genre-classification
- Engine: BTPE

---

## 4. Index Source

The workflow index is defined in:
workflow/index/workflow_index.py

It is populated automatically by the workflow registry and autodiscovery system.

---

## 5. Status

The Workflow Index is fully operational and integrated with:
- WorkflowEngine
- WorkflowRegistry
- Autodiscovery
- CLI workflow commands
- Semantic metadata
- Schema validation
- Documentation layer
