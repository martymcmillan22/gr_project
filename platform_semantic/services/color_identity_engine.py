"""Deterministic global-unique color identity engine.

This module separates two concerns:

1) Identity layer (collision-free, reversible):
   color_code = (compartment_id << 20) | local_index

2) Presentation layer (human-facing semantic color):
   Maps local_index into a compartment-specific 64x64x64 anchor band using
   Morton/Z-order deinterleave for local spatial coherence.

Identity RGB is always reversible back to color_code. Display RGB is semantic
and may be many-to-one for a compartment because the anchor band has 18 bits of
capacity while local_index has 20 bits.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any

COMPARTMENT_COUNT = 16
LOCAL_INDEX_BITS = 20
LOCAL_INDEX_MAX = (1 << LOCAL_INDEX_BITS) - 1
COLOR_CODE_BITS = 24
COLOR_CODE_MAX = (1 << COLOR_CODE_BITS) - 1
MORTON_BITS_PER_CHANNEL = 6
MORTON_VALUE_MAX = (1 << MORTON_BITS_PER_CHANNEL) - 1
MORTON_INDEX_BITS = 18
MORTON_INDEX_MASK = (1 << MORTON_INDEX_BITS) - 1

INDUSTRY_INDEX_BITS = 2
SUBINDUSTRY_INDEX_BITS = 2
NODE_INDEX_BITS = 16
INDUSTRY_INDEX_MAX = (1 << INDUSTRY_INDEX_BITS) - 1
SUBINDUSTRY_INDEX_MAX = (1 << SUBINDUSTRY_INDEX_BITS) - 1
NODE_INDEX_MAX = (1 << NODE_INDEX_BITS) - 1

CATALOG_PATH = Path(__file__).resolve().parents[1] / "catalogs" / "macro_map.json"


@dataclass(frozen=True)
class AnchorBand:
    """64-step channel anchor for semantic display RGB."""

    r0: int
    g0: int
    b0: int

    def validate(self) -> None:
        for value in (self.r0, self.g0, self.b0):
            if value < 0 or value > 192:
                raise ValueError("Anchor channel starts must be in [0, 192].")

    def apply(self, r6: int, g6: int, b6: int) -> tuple[int, int, int]:
        return self.r0 + r6, self.g0 + g6, self.b0 + b6


# 16 deterministic anchor bands (all 64^3 cubes).
# The compartment IDs map to the canonical subjects in order:
# 0 Math, 1 Language, 2 Arts, 3 Science,
# 4 General Information, 5 Literature, 6 Crafts, 7 Technology,
# 8 History, 9 Geography, 10 Architecture, 11 Ecology,
# 12 Philosophy, 13 Law and Governance, 14 Economics, 15 Systemics.
COMPARTMENTS: dict[int, dict[str, Any]] = {
    0: {"subject": "Math", "phase": "Primary", "label": "Red", "group_id": 1, "sector_id": 1},
    1: {"subject": "Language", "phase": "Primary", "label": "Blue", "group_id": 2, "sector_id": 1},
    2: {"subject": "Arts", "phase": "Primary", "label": "Yellow", "group_id": 3, "sector_id": 1},
    3: {"subject": "Science", "phase": "Primary", "label": "Green", "group_id": 4, "sector_id": 1},
    4: {"subject": "General Information", "phase": "Secondary", "label": "Purple", "group_id": 5, "sector_id": 2},
    5: {"subject": "Literature", "phase": "Secondary", "label": "Teal", "group_id": 6, "sector_id": 2},
    6: {"subject": "Crafts", "phase": "Secondary", "label": "Orange", "group_id": 7, "sector_id": 2},
    7: {"subject": "Technology", "phase": "Secondary", "label": "Lime", "group_id": 8, "sector_id": 2},
    8: {"subject": "History", "phase": "Tertiary", "label": "Red-Purple", "group_id": 9, "sector_id": 3},
    9: {"subject": "Geography", "phase": "Tertiary", "label": "Blue-Teal", "group_id": 10, "sector_id": 3},
    10: {"subject": "Architecture", "phase": "Tertiary", "label": "Yellow-Orange", "group_id": 11, "sector_id": 3},
    11: {"subject": "Ecology", "phase": "Tertiary", "label": "Green-Lime", "group_id": 12, "sector_id": 3},
    12: {"subject": "Philosophy", "phase": "Meta", "label": "Deep Crimson", "group_id": 13, "sector_id": 4},
    13: {"subject": "Law and Governance", "phase": "Meta", "label": "Deep Indigo", "group_id": 14, "sector_id": 4},
    14: {"subject": "Economics", "phase": "Meta", "label": "Gold-Ochre", "group_id": 15, "sector_id": 4},
    15: {"subject": "Systemics", "phase": "Meta", "label": "Deep Forest", "group_id": 16, "sector_id": 4},
}

COMPARTMENT_ANCHOR_BANDS: dict[int, AnchorBand] = {
    0: AnchorBand(192, 0, 0),      # Red
    1: AnchorBand(0, 0, 192),      # Blue
    2: AnchorBand(192, 192, 0),    # Yellow
    3: AnchorBand(0, 192, 0),      # Green
    4: AnchorBand(192, 0, 192),    # Purple
    5: AnchorBand(0, 192, 192),    # Teal
    6: AnchorBand(128, 64, 0),     # Orange
    7: AnchorBand(64, 192, 0),     # Lime
    8: AnchorBand(128, 0, 128),    # Red-Purple
    9: AnchorBand(0, 128, 192),    # Blue-Teal
    10: AnchorBand(192, 128, 0),   # Yellow-Orange
    11: AnchorBand(64, 192, 64),   # Green-Lime
    12: AnchorBand(192, 0, 64),    # Deep Crimson
    13: AnchorBand(64, 0, 128),    # Deep Indigo
    14: AnchorBand(192, 128, 64),  # Gold-Ochre
    15: AnchorBand(0, 128, 64),    # Deep Forest
}


def _normalize_lookup_key(value: str) -> str:
    return " ".join(str(value or "").strip().casefold().split())


@lru_cache(maxsize=1)
def _load_macro_map_catalog() -> dict[str, Any]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sectors"), list):
        raise ValueError("Invalid macro_map catalog payload.")
    return payload


@lru_cache(maxsize=1)
def _build_ontology_lookup() -> dict[tuple[str, str, str, str], tuple[int, int, int]]:
    """Build lookup key -> (compartment_id, industry_index, subindustry_index).

    Groups are included up to COMPARTMENT_COUNT by group_id -> compartment_id mapping.
    """

    catalog = _load_macro_map_catalog()
    lookup: dict[tuple[str, str, str, str], tuple[int, int, int]] = {}

    for sector in catalog["sectors"]:
        sector_id = int(sector["sector_id"])
        sector_name = str(sector["sector_name"])
        sector_aliases = {
            _normalize_lookup_key(sector_name),
            _normalize_lookup_key(sector_name.split("(")[0]),
            _normalize_lookup_key(f"sector {sector_id}"),
        }

        for group in sector.get("industry_groups", []):
            group_id = int(group["group_id"])
            if group_id < 1 or group_id > COMPARTMENT_COUNT:
                continue

            compartment_id = group_id - 1
            subject_name = str(group["subject_name"])
            subject_key = _normalize_lookup_key(subject_name)

            for industry_index, industry in enumerate(group.get("industries", [])):
                industry_name = str(industry["industry_name"])
                industry_key = _normalize_lookup_key(industry_name)

                for subindustry_index, subindustry_name in enumerate(industry.get("sub_industries", [])):
                    subindustry_key = _normalize_lookup_key(str(subindustry_name))
                    for sector_key in sector_aliases:
                        lookup[(sector_key, subject_key, industry_key, subindustry_key)] = (
                            compartment_id,
                            industry_index,
                            subindustry_index,
                        )

    return lookup


def _validate_compartment_id(compartment_id: int) -> None:
    if compartment_id < 0 or compartment_id >= COMPARTMENT_COUNT:
        raise ValueError(f"compartment_id must be in [0, {COMPARTMENT_COUNT - 1}].")


def _validate_local_index(local_index: int) -> None:
    if local_index < 0 or local_index > LOCAL_INDEX_MAX:
        raise ValueError(f"local_index must be in [0, {LOCAL_INDEX_MAX}].")


def _validate_color_code(color_code: int) -> None:
    if color_code < 0 or color_code > COLOR_CODE_MAX:
        raise ValueError(f"color_code must be in [0, {COLOR_CODE_MAX}].")


def _validate_industry_index(industry_index: int) -> None:
    if industry_index < 0 or industry_index > INDUSTRY_INDEX_MAX:
        raise ValueError(f"industry_index must be in [0, {INDUSTRY_INDEX_MAX}].")


def _validate_subindustry_index(subindustry_index: int) -> None:
    if subindustry_index < 0 or subindustry_index > SUBINDUSTRY_INDEX_MAX:
        raise ValueError(f"subindustry_index must be in [0, {SUBINDUSTRY_INDEX_MAX}].")


def _validate_node_index(node_index: int) -> None:
    if node_index < 0 or node_index > NODE_INDEX_MAX:
        raise ValueError(f"node_index must be in [0, {NODE_INDEX_MAX}].")


def get_compartment_metadata(compartment_id: int) -> dict[str, Any]:
    _validate_compartment_id(compartment_id)
    metadata = dict(COMPARTMENTS[compartment_id])
    metadata["compartment_id"] = compartment_id
    band = COMPARTMENT_ANCHOR_BANDS[compartment_id]
    metadata["display_anchor_band"] = {
        "r": [band.r0, band.r0 + 63],
        "g": [band.g0, band.g0 + 63],
        "b": [band.b0, band.b0 + 63],
    }
    return metadata


def build_local_index(industry_index: int, subindustry_index: int, node_index: int) -> int:
    """Pack 2-bit industry, 2-bit subindustry, and 16-bit node index."""

    _validate_industry_index(industry_index)
    _validate_subindustry_index(subindustry_index)
    _validate_node_index(node_index)
    return (
        (industry_index << (SUBINDUSTRY_INDEX_BITS + NODE_INDEX_BITS))
        | (subindustry_index << NODE_INDEX_BITS)
        | node_index
    )


def split_local_index(local_index: int) -> tuple[int, int, int]:
    """Unpack local index into (industry_index, subindustry_index, node_index)."""

    _validate_local_index(local_index)
    industry_index = (local_index >> (SUBINDUSTRY_INDEX_BITS + NODE_INDEX_BITS)) & INDUSTRY_INDEX_MAX
    subindustry_index = (local_index >> NODE_INDEX_BITS) & SUBINDUSTRY_INDEX_MAX
    node_index = local_index & NODE_INDEX_MAX
    return industry_index, subindustry_index, node_index


def resolve_ontology_path_to_indices(
    sector: str,
    subject: str,
    industry: str,
    subindustry: str,
) -> tuple[int, int, int]:
    """Resolve ontology path into (compartment_id, industry_index, subindustry_index)."""

    key = (
        _normalize_lookup_key(sector),
        _normalize_lookup_key(subject),
        _normalize_lookup_key(industry),
        _normalize_lookup_key(subindustry),
    )
    lookup = _build_ontology_lookup()
    resolved = lookup.get(key)
    if resolved is None:
        raise ValueError(
            "Unknown ontology path for color identity lattice. "
            "Ensure sector/subject/industry/subindustry matches platform_semantic/catalogs/macro_map.json "
            f"and that group_id is within 1..{COMPARTMENT_COUNT}."
        )
    return resolved


def encode_ontology_path(
    sector: str,
    subject: str,
    industry: str,
    subindustry: str,
    node_index: int = 0,
) -> dict[str, Any]:
    """Encode ontology path + node index into identity/display payload."""

    _validate_node_index(node_index)
    compartment_id, industry_index, subindustry_index = resolve_ontology_path_to_indices(
        sector=sector,
        subject=subject,
        industry=industry,
        subindustry=subindustry,
    )
    local_index = build_local_index(industry_index, subindustry_index, node_index)
    payload = encode_identity_and_display(compartment_id=compartment_id, local_index=local_index)
    payload["compartment"] = get_compartment_metadata(compartment_id)
    payload["path"] = {
        "sector": sector,
        "subject": subject,
        "industry": industry,
        "subindustry": subindustry,
        "industry_index": industry_index,
        "subindustry_index": subindustry_index,
        "node_index": node_index,
    }
    return payload


def encode_color_code(compartment_id: int, local_index: int) -> int:
    """Encode compartment + local index into a reversible 24-bit color code."""

    _validate_compartment_id(compartment_id)
    _validate_local_index(local_index)
    return (compartment_id << LOCAL_INDEX_BITS) | local_index


def decode_color_code(color_code: int) -> tuple[int, int]:
    """Decode a 24-bit color code into (compartment_id, local_index)."""

    _validate_color_code(color_code)
    compartment_id = color_code >> LOCAL_INDEX_BITS
    local_index = color_code & LOCAL_INDEX_MAX
    return compartment_id, local_index


def identity_rgb_from_color_code(color_code: int) -> tuple[int, int, int]:
    """Lossless identity RGB encoding of the 24-bit color code."""

    _validate_color_code(color_code)
    r = (color_code >> 16) & 0xFF
    g = (color_code >> 8) & 0xFF
    b = color_code & 0xFF
    return r, g, b


def color_code_from_identity_rgb(r: int, g: int, b: int) -> int:
    """Inverse of identity_rgb_from_color_code."""

    for value, channel in ((r, "r"), (g, "g"), (b, "b")):
        if value < 0 or value > 255:
            raise ValueError(f"{channel} must be in [0, 255].")
    return (r << 16) | (g << 8) | b


def morton_deinterleave_18(index_18: int) -> tuple[int, int, int]:
    """Decode 18-bit Morton index into 3 x 6-bit coordinates.

    Bit layout consumed from LSB upward by triples:
      bit 0 -> r bit 0, bit 1 -> g bit 0, bit 2 -> b bit 0,
      bit 3 -> r bit 1, bit 4 -> g bit 1, bit 5 -> b bit 1, ...
    """

    if index_18 < 0 or index_18 > MORTON_INDEX_MASK:
        raise ValueError(f"index_18 must be in [0, {MORTON_INDEX_MASK}].")

    r6 = 0
    g6 = 0
    b6 = 0
    for bit in range(MORTON_BITS_PER_CHANNEL):
        r6 |= ((index_18 >> (3 * bit)) & 0b1) << bit
        g6 |= ((index_18 >> (3 * bit + 1)) & 0b1) << bit
        b6 |= ((index_18 >> (3 * bit + 2)) & 0b1) << bit
    return r6, g6, b6


def morton_interleave_18(r6: int, g6: int, b6: int) -> int:
    """Encode 3 x 6-bit coordinates into 18-bit Morton index.

    This is useful for testing invertibility and deterministic round-trips.
    """

    for value, name in ((r6, "r6"), (g6, "g6"), (b6, "b6")):
        if value < 0 or value > MORTON_VALUE_MAX:
            raise ValueError(f"{name} must be in [0, {MORTON_VALUE_MAX}].")

    index_18 = 0
    for bit in range(MORTON_BITS_PER_CHANNEL):
        index_18 |= ((r6 >> bit) & 0b1) << (3 * bit)
        index_18 |= ((g6 >> bit) & 0b1) << (3 * bit + 1)
        index_18 |= ((b6 >> bit) & 0b1) << (3 * bit + 2)
    return index_18


def display_rgb(compartment_id: int, local_index: int) -> tuple[int, int, int]:
    """Human-facing semantic display RGB for a compartment-local node.

    The top 2 bits of local_index are currently reserved as display variants
    and are not used for uniqueness; the lower 18 bits drive Morton traversal
    in the 64x64x64 anchor band.
    """

    _validate_compartment_id(compartment_id)
    _validate_local_index(local_index)

    band = COMPARTMENT_ANCHOR_BANDS[compartment_id]
    band.validate()

    morton_index = local_index & MORTON_INDEX_MASK
    r6, g6, b6 = morton_deinterleave_18(morton_index)
    return band.apply(r6, g6, b6)


def encode_identity_and_display(
    compartment_id: int,
    local_index: int,
) -> dict[str, object]:
    """Convenience helper for callers that need both identity and display."""

    color_code = encode_color_code(compartment_id, local_index)
    identity_rgb = identity_rgb_from_color_code(color_code)
    display = display_rgb(compartment_id, local_index)
    industry_index, subindustry_index, node_index = split_local_index(local_index)
    return {
        "compartment_id": compartment_id,
        "local_index": local_index,
        "color_code": color_code,
        "identity_rgb": identity_rgb,
        "display_rgb": display,
        "local_index_fields": {
            "industry_index": industry_index,
            "subindustry_index": subindustry_index,
            "node_index": node_index,
        },
        "compartment": get_compartment_metadata(compartment_id),
    }
