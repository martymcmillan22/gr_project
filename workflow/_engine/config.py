from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = WORKFLOW_ROOT / "registry.json"

CATEGORY_DIRS = {
    "erd": WORKFLOW_ROOT / "database_design" / "mermaid_erds",
    "sequence": WORKFLOW_ROOT / "logic_design" / "mermaid_sequences",
    "ui_template": WORKFLOW_ROOT / "ui_templates" / "penpot_templates" / "features",
    "ui_component": WORKFLOW_ROOT / "ui_components" / "penpot_components" / "features",
}
