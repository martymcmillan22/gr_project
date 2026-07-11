import hashlib

from .branch_resolver import resolve_identity_branch
from .typing import IdentityPayload


def compile_cpndc_identity(project: IdentityPayload) -> dict[str, object]:
    slug = project["slug"].strip().lower()
    canonical_key = "|".join(
        [
            slug,
            project["semantic_intent"].strip(),
            project["mlas_tier"].strip(),
            project["btif_classification"].strip(),
        ]
    )
    identity_hash = hashlib.sha256(canonical_key.encode("utf-8")).hexdigest()[:16]

    semantic_tags = sorted({tag.strip().lower() for tag in project.get("semantic_tags", []) if tag.strip()})
    drift_risk = project.get("drift_risk")
    branch_resolution = resolve_identity_branch(project, drift_risk=drift_risk)

    return {
        "identity_uri": f"cpndc://project-middle-layer/{slug}",
        "lineage": f"workflow/{slug}",
        "identity_id": f"pmid-{identity_hash}",
        "canonical_key": canonical_key,
        "name": project.get("name", slug.replace("-", " ").title()),
        "semantic_intent": project["semantic_intent"],
        "mlas_tier": project["mlas_tier"],
        "btif_classification": project["btif_classification"],
        "semantic_tags": semantic_tags,
        "branches": {
            "idea_seed_project": f"cpndc://branch/{slug}/idea-seed-project",
            "identity_specialization": f"cpndc://branch/{slug}/identity-specialization",
        },
        "branch_resolution": branch_resolution,
    }
