# Creator Workflow CLI
Document ID: BTPE-CREATOR-CLI-001
Version: v1.0
Status: Active

---

## Commands

- `workflows` lists registered workflows
- `describe creator-workflow` shows manifest metadata
- `introspect creator-workflow` shows schema, metadata, and propagation class
- `creator-workflow --input-file <path>` executes the narrative creator pipeline

## Input Contract

The `creator-workflow` command expects a JSON payload produced by Strict Mode
or an equivalent validated QPU structure.
