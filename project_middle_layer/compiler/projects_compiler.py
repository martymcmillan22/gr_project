from pathlib import Path

from project_middle_layer.identity import compile_cpndc_identity
from project_middle_layer.schemas import ProjectSchema


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def compile_project_middle_layer_payload(schema: ProjectSchema) -> dict[str, object]:
    root = _repo_root()
    slug = schema["slug"]

    generated_paths = {
        "erd": root / f"workflow/database_design/mermaid_erds/{slug}.erd.mmd",
        "sequence": root / f"workflow/logic_design/mermaid_sequences/{slug}.sequence.mmd",
        "models": root / f"platform_core/workflow_generated/models/{slug}_models.py",
        "logic": root / f"platform_core/workflow_generated/logic/{slug}_logic.py",
    }

    identity = compile_cpndc_identity(
        {
            "slug": schema["slug"],
            "name": schema["name"],
            "semantic_intent": schema["semantic_intent"],
            "mlas_tier": schema["mlas_tier"],
            "btif_classification": schema["btif_classification"],
            "semantic_tags": schema["semantic_tags"],
        }
    )

    return {
        "project": schema,
        "identity": identity,
        "generated_artifacts": {key: str(path) for key, path in generated_paths.items()},
        "artifact_status": {key: path.exists() for key, path in generated_paths.items()},
    }
