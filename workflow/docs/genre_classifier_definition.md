# Genre Classifier Definition
Document ID: BTPE-GENRE-DEF-001
Version: v1.0
Status: Active

---

## 1. Definition File

workflow/definitions/genre_classifier.workflow.json

## 2. Node Graph

1. signal_extraction_node
2. genre_rule_engine_node
3. classification_output_node

## 3. Execution Contract

Entrypoint: signal_extraction_node
Endpoint: classification_output_node

## 4. Engine + Semantic Files

- Engine: workflow/engine/genre_classifier_engine.py
- Schema: workflow/schema/genre_classifier_schema.py
- Metadata: workflow/metadata/genre_classifier_metadata.py
- Propagation: workflow/propagation/genre_classifier_propagation.py
