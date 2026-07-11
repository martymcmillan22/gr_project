from pathlib import Path
from typing import Any

from .btif_router import assign_btif_route, build_btif_routing_table
from .mlas_integration import build_mlas_report


def _write(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path.as_posix()


def _feature_header(feature: dict[str, Any]) -> list[str]:
    return [
        f"%% feature: {feature.get('name', '')}",
        f"%% slug: {feature.get('slug', '')}",
        f"%% mlas_tier: {feature.get('mlas_tier', '')}",
        f"%% btif_classification: {feature.get('btif_classification', '')}",
    ]


def render_feature_erd_relationship(feature: dict[str, Any]) -> str:
    slug = str(feature.get("slug", ""))
    erd_path = feature.get("paths", {}).get("erd", "")
    lines = ["graph TD", *_feature_header(feature)]
    lines.extend(
        [
            f"    FEATURE_{slug.replace('-', '_')}[{slug}] --> ERD[{erd_path}]",
            "    ERD --> ENTITY[FEATURE_ENTITY]",
            "    ENTITY --> FIELD_ID[id]",
            "    ENTITY --> FIELD_NAME[name]",
        ]
    )
    return "\n".join(lines)


def render_feature_sequence_flow(feature: dict[str, Any]) -> str:
    sequence_path = feature.get("paths", {}).get("sequence", "")
    lines = ["sequenceDiagram", *_feature_header(feature)]
    lines.extend(
        [
            "    participant UI",
            "    participant API",
            "    participant Logic",
            f"    Note over UI,Logic: source {sequence_path}",
            "    UI->>API: Request",
            "    API->>Logic: Execute flow",
            "    Logic-->>API: Result",
            "    API-->>UI: Response",
        ]
    )
    return "\n".join(lines)


def render_feature_dependency_graph(feature: dict[str, Any]) -> str:
    slug = str(feature.get("slug", ""))
    paths = feature.get("paths", {})
    lines = ["graph LR", *_feature_header(feature)]
    lines.extend(
        [
            f"    REG[registry:{slug}] --> ERD[{paths.get('erd', '')}]",
            f"    REG --> SEQ[{paths.get('sequence', '')}]",
            f"    REG --> UIT[{paths.get('ui_template', '')}]",
            f"    REG --> UIC[{paths.get('ui_component', '')}]",
            "    ERD --> MODELS[platform_core/workflow_generated/models]",
            "    SEQ --> LOGIC[platform_core/workflow_generated/logic]",
            "    UIT --> PAGES[ui_apps/workflow_generated/pages]",
            "    UIC --> DSGEN[workflow/ui_components/penpot_components/generated]",
        ]
    )
    return "\n".join(lines)


def render_feature_semantic_map(feature: dict[str, Any]) -> str:
    slug = str(feature.get("slug", ""))
    mlas_tier = str(feature.get("mlas_tier", ""))
    semantic_intent = str(feature.get("semantic_intent", ""))
    btif_classification = str(feature.get("btif_classification", ""))
    btif_route = assign_btif_route(feature)
    tags = feature.get("semantic_tags", [])

    lines = ["graph TD", *_feature_header(feature)]
    lines.extend(
        [
            f"    FEATURE[{slug}] --> MLAS[{mlas_tier}]",
            f"    FEATURE --> INTENT[{semantic_intent}]",
            f"    FEATURE --> BTIF_CLASS[{btif_classification}]",
            f"    BTIF_CLASS --> BTIF_ROUTE[{btif_route}]",
        ]
    )
    for tag in tags:
        safe = str(tag).replace(" ", "-")
        lines.append(f"    FEATURE --> TAG_{safe}[tag:{tag}]")
    return "\n".join(lines)


def render_feature_visual_bundle(feature: dict[str, Any]) -> str:
    parts = [
        "# Workflow Feature Visualization",
        "",
        "## ERD Relationships",
        "```mermaid",
        render_feature_erd_relationship(feature),
        "```",
        "",
        "## Sequence Flow",
        "```mermaid",
        render_feature_sequence_flow(feature),
        "```",
        "",
        "## Dependency Graph",
        "```mermaid",
        render_feature_dependency_graph(feature),
        "```",
        "",
        "## Semantic Classification Map",
        "```mermaid",
        render_feature_semantic_map(feature),
        "```",
    ]
    return "\n".join(parts)


def render_global_mlas_tier_map(registry: dict[str, Any]) -> str:
    mlas_rows = build_mlas_report(registry)
    lines = ["graph LR", "    ROOT[MLAS Tiers]"]
    for row in mlas_rows:
        slug = row.get("slug", "")
        tier = row.get("mlas_tier", "")
        lines.append(f"    ROOT --> TIER_{slug.replace('-', '_')}[{tier}:{slug}]")
    return "\n".join(lines)


def render_global_btif_routing_map(registry: dict[str, Any]) -> str:
    routes = build_btif_routing_table(registry)
    lines = ["graph LR", "    ROOT[BTIF Routes]"]
    for row in routes:
        slug = row.get("slug", "")
        route = row.get("route", "")
        lines.append(f"    ROOT --> ROUTE_{slug.replace('-', '_')}[{route}]")
    return "\n".join(lines)


def render_global_feature_graph(registry: dict[str, Any]) -> str:
    lines = ["graph TD", "    WORKFLOW[workflow registry]"]
    for feature in registry.get("features", []):
        slug = str(feature.get("slug", ""))
        lines.append(f"    WORKFLOW --> FEATURE_{slug.replace('-', '_')}[{slug}]")
    return "\n".join(lines)


def write_feature_visualization(feature: dict[str, Any], workflow_root: Path) -> str:
    slug = str(feature.get("slug", "")).strip()
    out_dir = workflow_root / "visualizations" / "features"
    out_path = out_dir / f"{slug}.visualization.md"
    content = render_feature_visual_bundle(feature)
    return _write(out_path, content)


def write_global_visualizations(registry: dict[str, Any], workflow_root: Path) -> dict[str, str]:
    out_dir = workflow_root / "visualizations"
    mlas_path = out_dir / "mlas-tier-map.mmd"
    btif_path = out_dir / "btif-routing-map.mmd"
    feature_path = out_dir / "feature-dependency-graph.mmd"

    return {
        "mlas_tier_map": _write(mlas_path, render_global_mlas_tier_map(registry)),
        "btif_routing_map": _write(btif_path, render_global_btif_routing_map(registry)),
        "feature_dependency_graph": _write(feature_path, render_global_feature_graph(registry)),
    }
