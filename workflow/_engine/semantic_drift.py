from pathlib import Path
from typing import Any

from .btif_router import assign_btif_route
from .mlas_integration import normalize_semantic_tags


def _check_file_contains(path: Path, needles: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return all(needle in text for needle in needles)


def detect_feature_drift(feature: dict[str, Any], workflow_root: Path, repo_root: Path) -> list[dict[str, str]]:
    drift: list[dict[str, str]] = []
    slug = str(feature.get("slug", "")).strip()
    if not slug:
        return [{"type": "feature", "reason": "missing slug", "severity": "high"}]

    propagation = feature.get("propagation", {})
    mlas_block = propagation.get("mlas", {}) if isinstance(propagation, dict) else {}

    expected_tags = ",".join(normalize_semantic_tags(feature.get("semantic_tags", [])))
    observed_tags = str(mlas_block.get("semantic_tags", ""))
    if expected_tags and observed_tags and expected_tags != observed_tags:
        drift.append(
            {
                "type": "semantic_tags",
                "reason": f"expected '{expected_tags}' observed '{observed_tags}'",
                "severity": "medium",
            }
        )

    expected_mlas_tier = str(feature.get("mlas_tier", "")).strip()
    observed_mlas_tier = str(mlas_block.get("mlas_tier", "")).strip()
    if expected_mlas_tier and observed_mlas_tier and expected_mlas_tier != observed_mlas_tier:
        drift.append(
            {
                "type": "mlas_tier",
                "reason": f"expected '{expected_mlas_tier}' observed '{observed_mlas_tier}'",
                "severity": "high",
            }
        )

    expected_route = assign_btif_route(feature)
    observed_route = str(propagation.get("btif_route", "")) if isinstance(propagation, dict) else ""
    if observed_route and observed_route != expected_route:
        drift.append(
            {
                "type": "btif_route",
                "reason": f"expected '{expected_route}' observed '{observed_route}'",
                "severity": "high",
            }
        )

    paths = feature.get("paths", {})
    erd_path = workflow_root / str(paths.get("erd", ""))
    seq_path = workflow_root / str(paths.get("sequence", ""))
    template_path = workflow_root / str(paths.get("ui_template", ""))
    component_path = workflow_root / str(paths.get("ui_component", ""))

    if not erd_path.exists():
        drift.append({"type": "erd", "reason": f"missing artifact {erd_path.as_posix()}", "severity": "high"})
    elif not _check_file_contains(erd_path, [f"%% slug: {slug}"]):
        drift.append({"type": "erd", "reason": "slug marker missing in ERD", "severity": "medium"})

    if not seq_path.exists():
        drift.append({"type": "sequence", "reason": f"missing artifact {seq_path.as_posix()}", "severity": "high"})
    elif not _check_file_contains(seq_path, [f"%% slug: {slug}"]):
        drift.append({"type": "sequence", "reason": "slug marker missing in sequence", "severity": "medium"})

    if not template_path.exists():
        drift.append(
            {
                "type": "ui_template",
                "reason": f"missing artifact {template_path.as_posix()}",
                "severity": "high",
            }
        )

    if not component_path.exists():
        drift.append(
            {
                "type": "ui_component",
                "reason": f"missing artifact {component_path.as_posix()}",
                "severity": "high",
            }
        )

    synced = propagation.get("synced_targets", {}) if isinstance(propagation, dict) else {}
    for key in [
        "erd_backend_models",
        "sequence_backend_logic",
        "ui_template_react_page",
        "ui_component_design_system",
    ]:
        target = str(synced.get(key, ""))
        if target and not (repo_root / target).exists():
            drift.append(
                {
                    "type": "sync_target",
                    "reason": f"missing propagated target {target}",
                    "severity": "medium",
                }
            )

    return drift


def build_drift_report(registry: dict[str, Any], workflow_root: Path, repo_root: Path) -> dict[str, Any]:
    report: dict[str, Any] = {"features": {}}
    for feature in registry.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        drifts = detect_feature_drift(feature, workflow_root, repo_root)
        report["features"][slug] = {
            "drift_count": len(drifts),
            "drift": drifts,
        }
    return report
