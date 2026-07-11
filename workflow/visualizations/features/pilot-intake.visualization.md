# Workflow Feature Visualization

## ERD Relationships
```mermaid
graph TD
%% feature: Pilot Intake
%% slug: pilot-intake
%% mlas_tier: Semantic Utility
%% btif_classification: IntakeFlow
    FEATURE_pilot_intake[pilot-intake] --> ERD[database_design/mermaid_erds/pilot-intake.erd.mmd]
    ERD --> ENTITY[FEATURE_ENTITY]
    ENTITY --> FIELD_ID[id]
    ENTITY --> FIELD_NAME[name]
```

## Sequence Flow
```mermaid
sequenceDiagram
%% feature: Pilot Intake
%% slug: pilot-intake
%% mlas_tier: Semantic Utility
%% btif_classification: IntakeFlow
    participant UI
    participant API
    participant Logic
    Note over UI,Logic: source logic_design/mermaid_sequences/pilot-intake.sequence.mmd
    UI->>API: Request
    API->>Logic: Execute flow
    Logic-->>API: Result
    API-->>UI: Response
```

## Dependency Graph
```mermaid
graph LR
%% feature: Pilot Intake
%% slug: pilot-intake
%% mlas_tier: Semantic Utility
%% btif_classification: IntakeFlow
    REG[registry:pilot-intake] --> ERD[database_design/mermaid_erds/pilot-intake.erd.mmd]
    REG --> SEQ[logic_design/mermaid_sequences/pilot-intake.sequence.mmd]
    REG --> UIT[ui_templates/penpot_templates/features/pilot-intake/template.md]
    REG --> UIC[ui_components/penpot_components/features/pilot-intake/component.md]
    ERD --> MODELS[platform_core/workflow_generated/models]
    SEQ --> LOGIC[platform_core/workflow_generated/logic]
    UIT --> PAGES[ui_apps/workflow_generated/pages]
    UIC --> DSGEN[workflow/ui_components/penpot_components/generated]
```

## Semantic Classification Map
```mermaid
graph TD
%% feature: Pilot Intake
%% slug: pilot-intake
%% mlas_tier: Semantic Utility
%% btif_classification: IntakeFlow
    FEATURE[pilot-intake] --> MLAS[Semantic Utility]
    FEATURE --> INTENT[CaptureAndRoute]
    FEATURE --> BTIF_CLASS[IntakeFlow]
    BTIF_CLASS --> BTIF_ROUTE[btif://intakeflow/captureandroute/pilot-intake]
    FEATURE --> TAG_intake[tag:intake]
    FEATURE --> TAG_pilot[tag:pilot]
    FEATURE --> TAG_routing[tag:routing]
```
