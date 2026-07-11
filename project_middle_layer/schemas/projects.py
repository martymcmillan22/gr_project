import json
from pathlib import Path
from typing import Any, TypedDict


class ProjectSchema(TypedDict):
    slug: str
    name: str
    semantic_intent: str
    mlas_tier: str
    btif_classification: str
    semantic_tags: list[str]


def _schema_file_path() -> Path:
    return Path(__file__).with_name("projects.schema.json")


def get_projects_json_schema() -> dict[str, Any]:
    return json.loads(_schema_file_path().read_text(encoding="utf-8"))


def validate_project_schema_dict(project: ProjectSchema) -> list[str]:
    errors: list[str] = []
    required_fields = {
        "slug": str,
        "name": str,
        "semantic_intent": str,
        "mlas_tier": str,
        "btif_classification": str,
        "semantic_tags": list,
    }

    for field_name, field_type in required_fields.items():
        if field_name not in project:
            errors.append(f"Missing required field: {field_name}")
            continue
        if not isinstance(project[field_name], field_type):
            errors.append(f"Field {field_name} must be {field_type.__name__}")

    if "semantic_tags" in project and isinstance(project["semantic_tags"], list):
        if not project["semantic_tags"]:
            errors.append("semantic_tags must contain at least one value")
        elif any(not isinstance(tag, str) or not tag.strip() for tag in project["semantic_tags"]):
            errors.append("semantic_tags must only contain non-empty strings")

    return errors


def build_project_schema(
    slug: str,
    name: str,
    semantic_intent: str,
    mlas_tier: str,
    btif_classification: str,
    semantic_tags: list[str],
) -> ProjectSchema:
    return {
        "slug": slug,
        "name": name,
        "semantic_intent": semantic_intent,
        "mlas_tier": mlas_tier,
        "btif_classification": btif_classification,
        "semantic_tags": sorted({tag.strip().lower() for tag in semantic_tags if tag.strip()}),
    }
