import hashlib

from project_middle_layer.schemas import ProjectSchema


def compile_specialized_path(
    schema: ProjectSchema,
    *,
    tier_profile: dict[str, object],
    identity_payload: dict[str, object],
    drift_forecast: dict[str, object],
) -> dict[str, object]:
    identity = identity_payload.get("identity", {}) if isinstance(identity_payload, dict) else {}
    branch_resolution = identity.get("branch_resolution", {}) if isinstance(identity, dict) else {}

    selected_branch = str(branch_resolution.get("selected_branch", "specialization_branch"))
    risk_level = str(drift_forecast.get("risk", {}).get("risk_level", "medium"))

    final_form = {
        "form_type": "specialized_identity_form",
        "form_id": "spf-" + hashlib.sha1(f"{schema['slug']}|{selected_branch}".encode("utf-8")).hexdigest()[:12],
        "final_identity_uri": f"cpndc://final/{schema['slug']}/{selected_branch}",
        "deployment_path": f"runtime/project-middle-layer/{schema['slug']}/{selected_branch}",
        "branch": selected_branch,
        "risk_level": risk_level,
        "constraints": {
            "tier": tier_profile.get("tier"),
            "semantic_intent": schema["semantic_intent"],
            "btif_classification": schema["btif_classification"],
        },
    }

    return {
        "selected_branch": selected_branch,
        "forms": [final_form],
        "compile_status": "ready",
        "notes": [
            "Final identity forms are deterministic by slug + selected branch.",
            "Risk level informs release gating before production path activation.",
        ],
    }
