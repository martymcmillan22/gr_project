import json
from collections import Counter
from pathlib import Path

from project_middle_layer.schemas import ProjectSchema


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _safe_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def build_project_drift_forecast(schema: ProjectSchema, horizon_months: int = 12) -> dict[str, object]:
    root = _repo_root()
    registry_path = root / "workflow/meta/registry.json"
    annual_forecast_path = root / "workflow/reports/annual_semantic_drift_forecast.json"
    generic_forecast_path = root / "workflow/semantic_drift_forecast.json"

    registry = _safe_read_json(registry_path)
    global_forecast = _safe_read_json(annual_forecast_path) or _safe_read_json(generic_forecast_path)

    features = [feature for feature in registry.get("features", []) if isinstance(feature, dict)]
    all_tags: list[str] = []
    for feature in features:
        all_tags.extend(str(tag).strip().lower() for tag in feature.get("semantic_tags", []) if str(tag).strip())

    tag_counter = Counter(all_tags)
    project_tags = [str(tag).strip().lower() for tag in schema.get("semantic_tags", []) if str(tag).strip()]
    singleton_tags = [tag for tag in project_tags if tag_counter.get(tag, 0) <= 1]

    tag_volatility = (len(singleton_tags) / len(project_tags)) if project_tags else 1.0
    intent_risk = 0.25 if schema["semantic_intent"].strip() else 0.75
    lineage_risk = 0.3 if schema["slug"].strip() else 0.85

    local_risk = min(1.0, round((tag_volatility * 0.55) + (intent_risk * 0.25) + (lineage_risk * 0.20), 4))

    global_risk = (
        global_forecast.get("semantic_drift_forecast", {})
        .get("drift_forecast", {})
        .get("semantic_drift_risk")
    )
    if isinstance(global_risk, (float, int)):
        blended_risk = round(min(1.0, (local_risk * 0.65) + (float(global_risk) * 0.35)), 4)
    else:
        blended_risk = local_risk

    return {
        "horizon_months": horizon_months,
        "risk": {
            "local_project_drift_risk": local_risk,
            "blended_semantic_drift_risk": blended_risk,
            "risk_level": "high" if blended_risk >= 0.67 else "medium" if blended_risk >= 0.34 else "low",
        },
        "signals": {
            "project_tag_count": len(project_tags),
            "singleton_tag_count": len(singleton_tags),
            "singleton_tags": singleton_tags,
            "global_forecast_present": bool(global_forecast),
        },
        "recommended_actions": [
            "Normalize singleton tags before expansion apply mode",
            "Re-run semantic-scorecard after tier intent changes",
            "Review lineage and branch routing before specialized path compile",
        ],
    }
