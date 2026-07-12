# Genre Classifier Workflow
Document ID: BTPE-GENRE-001
Version: v1.0
Status: Active

---

## 1. Overview

Genre Classifier Workflow is a deterministic semantic workflow that consumes a
validated Strict Mode QPU and classifies narrative structure into a canonical
genre category.

## 2. Canonical Genres

- Action
- Drama
- Comedy
- Thriller
- Romance
- Sci-Fi
- Fantasy
- Mystery
- Horror

## 3. Input Signals

The workflow derives classification from these deterministic signals:

- inverse pair tension
- relay geometry
- SRL scaling curve
- temporal bias
- semantic tags

## 4. Output Contract

The workflow emits:

- genre
- confidence
- signals_used
- semantic_summary

## 5. Status

Genre Classifier is active and integrated with engine, registry, index, CLI,
debugger, introspection, test harness, and validation reporting.
