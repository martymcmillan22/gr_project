from .typing import IdentityPayload


def resolve_identity_branch(project: IdentityPayload, drift_risk: float | None = None) -> dict[str, object]:
    semantic_intent = project["semantic_intent"].strip().lower()
    mlas_tier = project["mlas_tier"].strip().lower()
    btif_classification = project["btif_classification"].strip().lower()
    slug = project["slug"].strip().lower()

    if drift_risk is not None and drift_risk >= 0.67:
        branch_key = "stabilization_branch"
        branch_reason = "High drift risk requires stability-first branch."
        confidence = 0.94
    elif "governance" in btif_classification:
        branch_key = "governance_branch"
        branch_reason = "BTIF classification indicates governance flow."
        confidence = 0.9
    elif (
        "expand" in semantic_intent
        or "integrate" in semantic_intent
        or "expansion" in btif_classification
        or "integration" in btif_classification
    ):
        branch_key = "expansion_integration_branch"
        branch_reason = "Intent/classification aligns with expansion and integration."
        confidence = 0.88
    elif "semantic utility" in mlas_tier:
        branch_key = "utility_branch"
        branch_reason = "MLAS tier indicates semantic utility branch policy."
        confidence = 0.84
    else:
        branch_key = "specialization_branch"
        branch_reason = "Fallback specialization branch for uncategorized semantics."
        confidence = 0.76

    return {
        "selected_branch": branch_key,
        "branch_uri": f"cpndc://branch/{slug}/{branch_key}",
        "lineage_path": f"workflow/{slug}/branches/{branch_key}",
        "confidence": confidence,
        "reason": branch_reason,
        "inputs": {
            "semantic_intent": project["semantic_intent"],
            "mlas_tier": project["mlas_tier"],
            "btif_classification": project["btif_classification"],
            "drift_risk": drift_risk,
        },
    }
