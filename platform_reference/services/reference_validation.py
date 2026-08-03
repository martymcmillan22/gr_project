import csv
from collections import Counter
from pathlib import Path

from django.core.management.base import CommandError

from platform_reference.models import GICSReference


PLACEHOLDER_HINTS = (
    "/absolute/path/",
    "/users/you/path/",
    "<path>",
    "your_gics.csv",
)


def validate_gics_csv(raw_path: str):
    """Validate a licensed GICS CSV file and return row totals by level."""
    if not raw_path:
        raise CommandError("Provide a GICS CSV path using --file <path> or positional filepath.")

    normalized_raw_path = raw_path.strip().lower()
    if any(hint in normalized_raw_path for hint in PLACEHOLDER_HINTS):
        raise CommandError(
            "Detected placeholder path. Use your actual licensed file path, e.g. "
            "python manage.py validate_gics_reference --file /Users/martymcmillan/Downloads/gics.csv"
        )

    file_path = Path(raw_path).expanduser().resolve()
    if not file_path.exists():
        raise CommandError(f"GICS file not found: {file_path}")

    required = {"code", "name", "level", "parent_code", "description", "source_version"}
    allowed_levels = {
        GICSReference.LEVEL_SECTOR,
        GICSReference.LEVEL_INDUSTRY_GROUP,
        GICSReference.LEVEL_INDUSTRY,
        GICSReference.LEVEL_SUB_INDUSTRY,
    }

    level_counter = Counter()
    pair_counter = Counter()
    codes_by_level = {level: set() for level in allowed_levels}
    rows = []

    with file_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = set(reader.fieldnames or [])
        if not required.issubset(fieldnames):
            raise CommandError(
                "GICS CSV missing required columns: code,name,level,parent_code,description,source_version"
            )

        for line_number, row in enumerate(reader, start=2):
            code = (row.get("code") or "").strip()
            name = (row.get("name") or "").strip()
            level = (row.get("level") or "").strip().lower()
            parent_code = (row.get("parent_code") or "").strip()
            source_version = (row.get("source_version") or "").strip()

            rows.append(
                {
                    "line": line_number,
                    "code": code,
                    "name": name,
                    "level": level,
                    "parent_code": parent_code,
                    "source_version": source_version,
                }
            )

            if code and level in allowed_levels:
                pair_counter[(code, level)] += 1
                level_counter[level] += 1
                codes_by_level[level].add(code)

    errors = []
    for row in rows:
        line_number = row["line"]
        code = row["code"]
        name = row["name"]
        level = row["level"]
        parent_code = row["parent_code"]
        source_version = row["source_version"]

        if not code:
            errors.append(f"line {line_number}: code is required")
            continue

        if not name:
            errors.append(f"line {line_number}: name is required for code {code}")

        if not source_version:
            errors.append(f"line {line_number}: source_version is required for code {code}")

        if level not in allowed_levels:
            errors.append(f"line {line_number}: unsupported GICS level '{level}' for code {code}")
            continue

        if pair_counter[(code, level)] > 1:
            errors.append(f"line {line_number}: duplicate code+level pair ({code}, {level})")

        if level != GICSReference.LEVEL_SECTOR and not parent_code:
            errors.append(f"line {line_number}: parent_code is required for level {level} (code {code})")

        if level == GICSReference.LEVEL_INDUSTRY_GROUP and parent_code and (
            parent_code not in codes_by_level[GICSReference.LEVEL_SECTOR]
        ):
            errors.append(
                f"line {line_number}: parent_code {parent_code} not found as sector for code {code}"
            )
        if level == GICSReference.LEVEL_INDUSTRY and parent_code and (
            parent_code not in codes_by_level[GICSReference.LEVEL_INDUSTRY_GROUP]
        ):
            errors.append(
                f"line {line_number}: parent_code {parent_code} not found as industry_group for code {code}"
            )
        if level == GICSReference.LEVEL_SUB_INDUSTRY and parent_code and (
            parent_code not in codes_by_level[GICSReference.LEVEL_INDUSTRY]
        ):
            errors.append(
                f"line {line_number}: parent_code {parent_code} not found as industry for code {code}"
            )

    if errors:
        preview = "\n".join(errors[:20])
        if len(errors) > 20:
            preview = f"{preview}\n... plus {len(errors) - 20} more errors"
        raise CommandError(f"GICS CSV validation failed with {len(errors)} error(s):\n{preview}")

    return {
        "rows": sum(level_counter.values()),
        "sector": level_counter[GICSReference.LEVEL_SECTOR],
        "industry_group": level_counter[GICSReference.LEVEL_INDUSTRY_GROUP],
        "industry": level_counter[GICSReference.LEVEL_INDUSTRY],
        "sub_industry": level_counter[GICSReference.LEVEL_SUB_INDUSTRY],
    }
