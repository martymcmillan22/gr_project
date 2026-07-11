from pathlib import Path


def _to_component_name(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("-")) + "Page"


def sync_ui_template_to_react_page(
    template_path: Path,
    slug: str,
    semantic_tags: list[str],
    repo_root: Path,
) -> str:
    component_name = _to_component_name(slug)

    out_dir = repo_root / "ui_apps" / "workflow_generated" / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{component_name}.tsx"

    tags = ", ".join(sorted(set(semantic_tags)))
    lines = [
        f"// source_template: {template_path.as_posix()}",
        f"// semantic_tags: {tags}",
        "",
        "import React from \"react\";",
        "",
        f"export default function {component_name}() {{",
        "    return (",
        "        <main data-workflow-generated=\"true\">",
        f"            <h1>{component_name}</h1>",
        f"            <p>Generated from workflow template for feature '{slug}'.</p>",
        "        </main>",
        "    );",
        "}",
    ]

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path.as_posix()
