# Strict Mode Workflow Documentation
Document ID: BTPE-WF-STRICT-001
Version: v1.0
Status: Active

---

## 1. Overview

Strict Mode is a deterministic 4-node workflow used to validate QPU structures
according to BaseTrue's semantic rules:

1. Inverse Pair Assembly  
2. Linear Relay Alignment  
3. SRL Scaling  
4. Temporal Mapping  

Strict Mode enforces the canonical QPU pattern:
- Two complete inverse pairs  
- Four-color contiguous relay segment  
- Four SRL values following x4 growth  
- Four temporal tenses in Past -> Present-Past -> Present-Future -> Future order  

---

## 2. Workflow Definition

Workflow ID: strict-mode  
Definition File: workflow/definitions/strict_mode.workflow.json  
Engine Module: workflow/engine/strict_mode_engine.py  
Schema File: workflow/semantic/strict_mode_qpu_schema.py  
Semantic Metadata: workflow/semantic/strict_mode_metadata.py  
Propagation Rules: workflow/semantic/strict_mode_propagation.py

---

## 3. Node Breakdown

### 3.1 Inverse Pair Node
File: inverse_pair_node.py  
Role: inverse-validation  
Description: Validates two complete inverse pairs.

### 3.2 Relay Alignment Node
File: relay_alignment_node.py  
Role: relay-validation  
Description: Ensures colors form a contiguous Linear Relay segment.

### 3.3 SRL Node
File: srl_node.py  
Role: srl-scaling  
Description: Validates SRL x4 growth across repositories.

### 3.4 Temporal Mapping Node
File: temporal_mapping_node.py  
Role: temporal-mapping  
Description: Maps relay segment to Past -> Present-Past -> Present-Future -> Future.

---

## 4. CLI Usage

```bash
python workflow/cli.py strict-mode \
--name "QPU Strict Mode" \
--inverse-pairs "red:green" "blue:yellow" \
--relay-segment "red blue yellow green" \
--srl-values 4 16 64 256 \
--tenses past present-past present-future future \
--btif-subjects Math Language Arts Science \
--semantic-tags strict qpu relay inverse temporal
```

---

## 5. QPU Schema Summary

Schema ID: strict-mode-qpu  
Required fields:
- inverse_pairs (2 pairs)
- relay_segment (4 colors)
- srl_values (4 integers)
- temporal_mapping (4 tenses)

Semantic bindings:
- workflow_id: strict-mode
- semantic_intent: QPU-Strict-Validation
- btif_subjects: MLAS lineage
- semantic_tags: strict, qpu, relay, inverse, temporal, srl

---

## 6. Error Pack

File: strict_mode_errors.py  
Error Codes:
- STRICT_INVERSE_MISSING
- STRICT_INVERSE_COUNT
- STRICT_RELAY_SEGMENT
- STRICT_SRL_GROWTH
- STRICT_TEMPORAL_COUNT
- STRICT_TEMPORAL_MAPPING

All Strict Mode errors inherit from StrictModeError.

---

## 7. Propagation Rules

File: strict_mode_propagation.py  
Outputs:
- strict_mode_enriched (metadata + QPU)
- btpe_layer (semantic layer for BTPE)

Propagation includes:
- semantic tags  
- intent  
- classification  
- BTIF lineage  
- node roles  

---

## 8. Example Output (Schema-Validated)

```json
{
  "workflow_id": "strict-mode",
  "semantic_intent": "QPU-Strict-Validation",
  "semantic_tags": ["strict", "qpu", "relay", "inverse", "temporal", "srl"],
  "btif_subjects": ["Math", "Language", "Arts", "Science"],
  "classification": {
    "type": "workflow",
    "tier": "strict",
    "category": "qpu-validation",
    "engine": "BTPE"
  },
  "qpu": {
    "inverse_pairs": [
      ["red", "green"],
      ["blue", "yellow"]
    ],
    "relay_segment": ["red", "blue", "yellow", "green"],
    "srl_values": [4, 16, 64, 256],
    "temporal_mapping": [
      "past",
      "present-past",
      "present-future",
      "future"
    ]
  }
}
```

---

## 9. Status

Strict Mode is fully integrated and ready for use across:
- CLI  
- Workflow Engine  
- BTPE Semantic Engine  
- BTIF Lineage Systems  
- Narrative Architecture Pipelines  
