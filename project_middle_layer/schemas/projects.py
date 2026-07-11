from typing import TypedDict


class ProjectSchema(TypedDict):
    slug: str
    name: str
    semantic_intent: str
    mlas_tier: str
    btif_classification: str
    semantic_tags: list[str]


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
