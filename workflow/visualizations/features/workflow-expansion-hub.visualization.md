# Workflow Feature Visualization

## ERD Relationships
```mermaid
graph TD
%% feature: Workflow Expansion Hub
%% slug: workflow-expansion-hub
%% mlas_tier: Semantic Utility
%% btif_classification: ExpansionFlow
    FEATURE_workflow_expansion_hub[workflow-expansion-hub] --> ERD[database_design/mermaid_erds/workflow-expansion-hub.erd.mmd]
    ERD --> ENTITY[FEATURE_ENTITY]
    ENTITY --> FIELD_ID[id]
    ENTITY --> FIELD_NAME[name]
```

## Sequence Flow
```mermaid
sequenceDiagram
%% feature: Workflow Expansion Hub
%% slug: workflow-expansion-hub
%% mlas_tier: Semantic Utility
%% btif_classification: ExpansionFlow
    participant UI
    participant API
    participant Logic
    Note over UI,Logic: source logic_design/mermaid_sequences/workflow-expansion-hub.sequence.mmd
    UI->>API: Request
    API->>Logic: Execute flow
    Logic-->>API: Result
    API-->>UI: Response
```

## Dependency Graph
```mermaid
graph LR
%% feature: Workflow Expansion Hub
%% slug: workflow-expansion-hub
%% mlas_tier: Semantic Utility
%% btif_classification: ExpansionFlow
    REG[registry:workflow-expansion-hub] --> ERD[database_design/mermaid_erds/workflow-expansion-hub.erd.mmd]
    REG --> SEQ[logic_design/mermaid_sequences/workflow-expansion-hub.sequence.mmd]
    REG --> UIT[ui_templates/penpot_templates/features/workflow-expansion-hub/template.md]
    REG --> UIC[ui_components/penpot_components/features/workflow-expansion-hub/component.md]
    ERD --> MODELS[platform_core/workflow_generated/models]
    SEQ --> LOGIC[platform_core/workflow_generated/logic]
    UIT --> PAGES[ui_apps/workflow_generated/pages]
    UIC --> DSGEN[workflow/ui_components/penpot_components/generated]
```

## Semantic Classification Map
```mermaid
graph TD
%% feature: Workflow Expansion Hub
%% slug: workflow-expansion-hub
%% mlas_tier: Semantic Utility
%% btif_classification: ExpansionFlow
    FEATURE[workflow-expansion-hub] --> MLAS[Semantic Utility]
    FEATURE --> INTENT[ExpandAndIntegrate]
    FEATURE --> BTIF_CLASS[ExpansionFlow]
    BTIF_CLASS --> BTIF_ROUTE[btif://expansionflow/expandandintegrate/workflow-expansion-hub]
    FEATURE --> TAG_expansion[tag:expansion]
    FEATURE --> TAG_integration[tag:integration]
    FEATURE --> TAG_workflow[tag:workflow]
```
