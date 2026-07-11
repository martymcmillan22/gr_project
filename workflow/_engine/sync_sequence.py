from pathlib import Path


def parse_sequence(sequence_path: Path) -> tuple[list[str], list[str]]:
    participants: list[str] = []
    messages: list[str] = []
    for raw_line in sequence_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("participant "):
            participants.append(line.replace("participant ", "", 1).strip())
        if "->>" in line or "-->>" in line:
            messages.append(line)
    return participants, messages


def sync_sequence_to_backend_logic_stub(
    sequence_path: Path,
    slug: str,
    semantic_intent: str,
    btif_route: str,
    repo_root: Path,
) -> str:
    participants, messages = parse_sequence(sequence_path)

    out_dir = repo_root / "platform_core" / "workflow_generated" / "logic"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}_logic.py"

    lines = [
        '"""Generated backend logic stubs from workflow sequence sync."""',
        "",
        f"# feature_slug: {slug}",
        f"# semantic_intent: {semantic_intent}",
        f"# btif_route: {btif_route}",
        f"# source_sequence: {sequence_path.as_posix()}",
        "",
        "def execute_flow(payload: dict) -> dict:",
        "    \"\"\"Deterministic flow stub mapped from sequence diagram.\"\"\"",
        "    return {",
        "        \"status\": \"ok\",",
        f"        \"feature\": \"{slug}\",",
        f"        \"semantic_intent\": \"{semantic_intent}\",",
        "        \"payload\": payload,",
        "    }",
        "",
        "# participants",
    ]

    for participant in participants:
        lines.append(f"# - {participant}")

    lines.append("")
    lines.append("# messages")
    for message in messages:
        lines.append(f"# - {message}")

    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out_path.as_posix()
