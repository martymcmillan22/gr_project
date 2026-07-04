from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import Slide


@dataclass(frozen=True)
class ResolvedRoute:
    phase_resolved: str
    metaphor: str
    ui_category_resolved: str
    layout_archetype: str
    component_pack: str
    nav_group: str
    page_signature: str
    color_primary: str


def _phase_defaults(phase: str) -> tuple[str, str]:
    defaults = {
        "create": ("immune_system", "operations"),
        "post": ("mycelium", "customer"),
        "work": ("botanist", "delivery"),
    }
    return defaults.get(phase, ("immune_system", "operations"))


def _derive_color(phase: str, subject: Optional[str], branch: Optional[str], fallback: str) -> str:
    subject_map = {
        "math": "red",
        "language": "blue",
        "arts": "yellow",
        "science": "green",
        "history": "pink",
        "geography": "cyan",
        "industry": "amber",
        "systems": "green-lime",
    }
    branch_map = {
        "sacp": "purple",
        "ednp": "teal",
        "vlsm": "orange",
        "mbsp": "lime",
    }

    if phase == "post" and branch:
        return branch_map.get(branch.lower(), fallback)
    if subject:
        return subject_map.get(subject.lower(), fallback)
    return fallback


def _layout_for_color(color: str) -> str:
    if color in {"red", "blue", "yellow", "green"}:
        return "matrix"
    if color in {"purple", "teal", "orange", "lime"}:
        return "journey"
    if color in {"pink", "cyan", "amber", "green-lime"}:
        return "pipeline"
    return "matrix"


def _component_pack(subject: Optional[str], branch: Optional[str], term: Optional[str], meta: Optional[str]) -> str:
    if meta:
        return "deep-pack"
    if term:
        return "structural-pack"
    if branch:
        return "narrative-pack"
    if subject:
        return "foundational-pack"
    return "foundational-pack"


def _nav_group(dewey_code: int) -> str:
    if 100 <= dewey_code <= 400:
        return "foundations"
    if 500 <= dewey_code <= 800:
        return "information"
    if 900 <= dewey_code <= 1000:
        return "systems"
    return "foundations"


def _page_signature(super_sector: Optional[str]) -> str:
    if not super_sector:
        return "operational"
    key = super_sector.lower()
    mapping = {
        "financials": "analytical",
        "communications": "narrative",
        "consumer": "experiential",
        "industrials": "operational",
    }
    return mapping.get(key, "operational")


def resolve_route(slide: Slide) -> ResolvedRoute:
    phase = (slide.phase or "create").lower()
    default_metaphor, default_category = _phase_defaults(phase)

    resolved_color = _derive_color(
        phase=phase,
        subject=slide.mlas_subject,
        branch=slide.mlas_branch,
        fallback=slide.color_primary,
    )

    return ResolvedRoute(
        phase_resolved=phase,
        metaphor=slide.metaphor or default_metaphor,
        ui_category_resolved=slide.ui_category or default_category,
        layout_archetype=_layout_for_color(resolved_color),
        component_pack=_component_pack(
            slide.mlas_subject,
            slide.mlas_branch,
            slide.mlas_term,
            slide.mlas_meta,
        ),
        nav_group=_nav_group(slide.dewey_code),
        page_signature=_page_signature(slide.industry_super_sector),
        color_primary=resolved_color,
    )


def apply_resolved_route(slide: Slide) -> Slide:
    resolved = resolve_route(slide)
    slide.phase_resolved = resolved.phase_resolved
    slide.metaphor = resolved.metaphor
    slide.ui_category_resolved = resolved.ui_category_resolved
    slide.layout_archetype = resolved.layout_archetype
    slide.component_pack = resolved.component_pack
    slide.nav_group = resolved.nav_group
    slide.page_signature = resolved.page_signature
    slide.color_primary = resolved.color_primary
    return slide
