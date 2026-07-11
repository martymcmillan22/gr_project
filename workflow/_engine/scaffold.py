from datetime import date
from pathlib import Path
import re

from .config import CATEGORY_DIRS


def slugify(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_feature_scaffold(name: str, slug: str, mlas_tier: str, btif_classification: str) -> dict[str, str]:
    today = date.today().isoformat()

    erd_path = CATEGORY_DIRS["erd"] / f"{slug}.erd.mmd"
    sequence_path = CATEGORY_DIRS["sequence"] / f"{slug}.sequence.mmd"
    ui_template_path = CATEGORY_DIRS["ui_template"] / slug / "template.md"
    ui_component_path = CATEGORY_DIRS["ui_component"] / slug / "component.md"

    _write(
        erd_path,
        "\n".join(
            [
                "erDiagram",
                f"    %% feature: {name}",
                f"    %% slug: {slug}",
                f"    %% mlas_tier: {mlas_tier}",
                f"    %% btif_classification: {btif_classification}",
                f"    %% generated: {today}",
                "    FEATURE_ENTITY {",
                "      string id PK",
                "      string name",
                "    }",
            ]
        )
        + "\n",
    )

    _write(
        sequence_path,
        "\n".join(
            [
                "sequenceDiagram",
                f"    %% feature: {name}",
                f"    %% slug: {slug}",
                f"    %% mlas_tier: {mlas_tier}",
                f"    %% btif_classification: {btif_classification}",
                f"    %% generated: {today}",
                "    participant UI",
                "    participant API",
                "    UI->>API: Request",
                "    API-->>UI: Response",
            ]
        )
        + "\n",
    )

    _write(
        ui_template_path,
        "\n".join(
            [
                f"# UI Template Scaffold: {name}",
                "",
                f"- slug: {slug}",
                f"- mlas_tier: {mlas_tier}",
                f"- btif_classification: {btif_classification}",
                f"- generated: {today}",
            ]
        )
        + "\n",
    )

    _write(
        ui_component_path,
        "\n".join(
            [
                f"# UI Component Scaffold: {name}",
                "",
                f"- slug: {slug}",
                f"- mlas_tier: {mlas_tier}",
                f"- btif_classification: {btif_classification}",
                f"- generated: {today}",
            ]
        )
        + "\n",
    )

    workflow_root = CATEGORY_DIRS["erd"].parents[1]
    return {
        "erd": str(erd_path.relative_to(workflow_root)),
        "sequence": str(sequence_path.relative_to(workflow_root)),
        "ui_template": str(ui_template_path.relative_to(workflow_root)),
        "ui_component": str(ui_component_path.relative_to(workflow_root)),
    }
