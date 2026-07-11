from pathlib import Path


def _to_component_name(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("-")) + "Card"


def sync_ui_component_to_design_system(
    component_spec_path: Path,
    slug: str,
    repo_root: Path,
) -> str:
    component_name = _to_component_name(slug)

    out_dir = repo_root / "workflow" / "ui_components" / "penpot_components" / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{component_name}.tsx"

    lines = [
        f"// source_component_spec: {component_spec_path.as_posix()}",
        "// tokens_source: workflow/ui_components/penpot_components/design-system/tokens-penpot-export.json",
        "",
        "import React from \"react\";",
        "",
        f"export function {component_name}() {{",
        "    return (",
        "        <section data-workflow-component=\"generated\">",
        f"            <strong>{component_name}</strong>",
        f"            <p>Generated design-system component for feature '{slug}'.</p>",
        "        </section>",
        "    );",
        "}",
    ]

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path.as_posix()
