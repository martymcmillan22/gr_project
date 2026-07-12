# BTPE Workflow Ecosystem — Master Overview
Document ID: BTPE-WF-ECOSYSTEM-001
Version: v1.0
Status: Active

---

## 1. Purpose

This document provides the master overview of the BTPE Workflow Ecosystem.
It describes how workflows are:

- defined  
- registered  
- discovered  
- executed  
- validated  
- documented  
- packaged  
- versioned  

Strict Mode is the reference implementation for the entire system.
Creator Workflow is the first non-validator workflow and demonstrates the
transition from correctness to deterministic narrative output.
Genre Classifier Workflow is the first semantic interpretation workflow and
demonstrates deterministic genre intelligence built on validated QPU output.

---

## 2. Core Architecture

The workflow ecosystem is composed of five primary layers:

1. **Definition Layer**  
   - strict_mode.workflow.json  
   - declarative workflow structure  
   - nodes, roles, semantic tags, classification  

2. **Engine Layer**  
   - workflow_engine.py  
   - dynamic engine loading  
   - schema validation  
   - semantic propagation  

3. **Registry Layer**  
   - workflow_registry.py  
   - global workflow catalog  
   - lookup + enumeration  

4. **Autodiscovery Layer**  
   - strict_mode_loader.py  
   - creator_workflow_loader.py  
   - automatic workflow registration  

5. **Documentation Layer**  
   - strict_mode.md  
   - strict_mode_cli.md  
   - workflow_index.md  
   - workflow_engine.md  
   - workflow_registry.md  
   - strict_mode_definition.md  
   - autodiscovery.md  
   - genre_classifier.md  
   - genre_classifier_cli.md  
   - genre_classifier_definition.md  

These layers form the foundation of BTPE’s workflow system.

---

## 3. Execution Pipeline

Workflow execution follows a deterministic pipeline:

1. Engine initialization  
2. Registry bootstrap  
3. Autodiscovery  
4. Manifest + index load  
5. Engine module import  
6. Engine instantiation  
7. Node execution  
8. Schema validation  
9. Semantic metadata attachment  
10. Propagation rules applied  

Strict Mode uses this pipeline to produce:

- QPU output  
- strict_mode_enriched  
- btpe_layer  

Creator Workflow uses this pipeline to produce:

- narrative output
- creator_enriched
- btpe_layer

Genre Classifier uses this pipeline to produce:

- genre classification output
- genre_classifier_enriched
- btpe_layer

---

## 4. CLI Integration

The CLI exposes workflow functionality through:

- `workflows`  
- `describe <workflow_id>`  
- `introspect <workflow_id>`  
- `strict-mode` execution  
- `creator-workflow` execution  
- `genre-classifier` execution  

These commands are powered by the central WorkflowEngine.

---

## 5. Developer Tools

The ecosystem includes four developer-grade modules:

1. **Workflow Debugger**  
   - node-level tracing  
   - schema diagnostics  
   - semantic inspection  

2. **Workflow Introspection API**  
   - manifest  
   - index  
   - schema  
   - metadata  
   - propagation  
   - engine module  

3. **Workflow Test Harness**  
   - deterministic regression tests  
   - schema validation  
   - semantic validation  

4. **Workflow Validation Report Generator**  
   - human-readable reports  
   - CI-ready output  

These tools make workflows fully inspectable, testable, and certifiable.

Creator Workflow uses the same tooling layer to expose narrative output,
outline structure, and semantic propagation data.
Genre Classifier uses the same tooling layer to expose classification signals,
confidence scoring, schema validation, and propagation diagnostics.

---

## 6. Packaging & Distribution

Workflows are packaged using:

workflow_package_manifest.py

creator_workflow_package_manifest.py

genre_classifier_package_manifest.py

Packaging metadata includes:

- version  
- classification  
- semantic tags  
- engine module  
- schema  
- metadata  
- propagation  
- documentation  
- compatibility  

This enables workflow distribution, installation, and marketplace integration.

---

## 7. Versioning & Changelog

Workflows follow deterministic semantic versioning:

MAJOR.MINOR.PATCH

Changelogs are stored under:

workflow/docs/changelog/<workflow_id>.md

Strict Mode uses:

strict_mode.md  
strict_mode_cli.md  
strict_mode_definition.md  
strict_mode_qpu_schema.py  
strict_mode_metadata.py  
strict_mode_propagation.py

All version sources must match.

---

## 8. Strict Mode — Reference Workflow

Strict Mode is the canonical example of a fully integrated workflow:

- definition  
- manifest  
- index  
- autodiscovery  
- registry  
- engine  
- schema  
- metadata  
- propagation  
- CLI  
- documentation  
- developer tools  
- packaging  
- versioning  

Creator Workflow is the first downstream workflow and demonstrates how BTPE
transitions from validation to narrative production.
Genre Classifier extends this stack into deterministic semantic classification,
enabling genre-aware transforms and generation workflows.

It demonstrates the complete workflow lifecycle.

---

## 9. Status

The BTPE Workflow Ecosystem is fully operational and integrated across:

- engine  
- registry  
- autodiscovery  
- CLI  
- semantic metadata  
- schema validation  
- developer tools  
- documentation  
- packaging  
- versioning  

Strict Mode is the first fully realized workflow in this ecosystem.
Creator Workflow and Genre Classifier are now fully integrated native workflows
in the same deterministic ecosystem.
