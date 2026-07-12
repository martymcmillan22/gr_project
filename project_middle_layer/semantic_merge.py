from __future__ import annotations


def merge_semantic_states(left: dict[str, object], right: dict[str, object], *, base: dict[str, object] | None = None) -> dict[str, object]:
    base_state = base or {}
    merged: dict[str, object] = dict(base_state)
    conflicts: list[dict[str, object]] = []

    keys = set(base_state.keys()) | set(left.keys()) | set(right.keys())
    for key in sorted(keys):
        base_value = base_state.get(key)
        left_value = left.get(key, base_value)
        right_value = right.get(key, base_value)

        if left_value == right_value:
            merged[key] = left_value
            continue

        if left_value == base_value:
            merged[key] = right_value
            continue

        if right_value == base_value:
            merged[key] = left_value
            continue

        conflicts.append(
            {
                "field": key,
                "left": left_value,
                "right": right_value,
                "base": base_value,
            }
        )

    return {
        "merged": merged,
        "conflicts": conflicts,
        "has_conflicts": bool(conflicts),
    }
