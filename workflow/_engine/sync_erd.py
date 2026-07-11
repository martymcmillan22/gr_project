from pathlib import Path
import re


ENTITY_PATTERN = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*\{")


def parse_erd_entities(erd_path: Path) -> list[str]:
    entities: list[str] = []
    for line in erd_path.read_text(encoding="utf-8").splitlines():
        match = ENTITY_PATTERN.match(line)
        if match:
            entities.append(match.group(1))
    return sorted(set(entities))


def _to_class_name(entity_name: str) -> str:
    return "".join(part.capitalize() for part in entity_name.lower().split("_"))


def sync_erd_to_backend_model_stub(erd_path: Path, slug: str, mlas_tier: str, repo_root: Path) -> str:
    entities = parse_erd_entities(erd_path)
    out_dir = repo_root / "platform_core" / "workflow_generated" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}_models.py"

    lines = [
        '"""Generated model stubs from workflow ERD sync."""',
        "",
        f"# feature_slug: {slug}",
        f"# mlas_tier: {mlas_tier}",
        f"# source_erd: {erd_path.as_posix()}",
        "",
    ]

    if not entities:
        lines.extend(
            [
                "# No entities were detected in ERD.",
                "class PlaceholderModel:",
                "    pass",
            ]
        )
    else:
        for entity in entities:
            class_name = _to_class_name(entity)
            lines.extend(
                [
                    f"class {class_name}:",
                    f"    \"\"\"Stub generated from ERD entity {entity}.\"\"\"",
                    "",
                    "    def __init__(self, id: str = \"\", name: str = \"\") -> None:",
                    "        self.id = id",
                    "        self.name = name",
                    "",
                ]
            )

    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out_path.as_posix()
