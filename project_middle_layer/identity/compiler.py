from .typing import IdentityPayload


def compile_cpndc_identity(project: IdentityPayload) -> dict[str, str]:
    slug = project["slug"].strip().lower()
    return {
        "identity_uri": f"cpndc://project-middle-layer/{slug}",
        "lineage": f"workflow/{slug}",
        "semantic_intent": project["semantic_intent"],
        "mlas_tier": project["mlas_tier"],
        "btif_classification": project["btif_classification"],
    }
