"""
RR (Repository Relay) service for PIP - the "yellow tier engine".

RR did not previously exist as backend code (confirmed during Phase 3
investigation - only the Penpot design artifact existed). This module handles
the Seed -> Project (seeds.Business) promotion, gated at CCPP tier, reusing
the existing SRL validation from Phase 2 (PIPSRLValidator) rather than
duplicating capacity/time_frame/tag logic.

NOTE: `seeds` already imports from `peringram.models`, so `peringram` must
never import from `seeds` at module load time (circular import). All
references to `seeds` below are local/deferred imports inside function bodies.

Scope note: "tagging" and "temporal routing" (mentioned in the Phase 3
checklist) are satisfied via the existing PIPSRLValidator tag-requirement
checks and pip_state.time_slot_time_frame exposure, respectively - no new
tag/temporal model or restriction is introduced here, since none was
concretely specified beyond what Phase 2 already built.

Project -> Enterprise promotion is explicitly deferred to Phase 4 (Enterprise
does not exist as a seeds lifecycle state yet).

Phase 4: RR now also requires a forward-looking Convection-Cycle slot
(present_future or future), in addition to CCPP+ tier - see
pip_state.rr_allowed_now / RRService.can_invoke().
"""

from functools import lru_cache
import json
from pathlib import Path

from .srl import PIPSRLValidator


class RRAccessDeniedError(Exception):
    """Raised when an RR action is attempted below the required tier."""


class RRService:
    """Gates and performs Seed -> Project (RR) promotions."""

    _CATALOG_PATH = Path(__file__).resolve().parents[1] / "platform_semantic" / "catalogs" / "macro_map.json"

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_macro_map_catalog():
        payload = json.loads(RRService._CATALOG_PATH.read_text(encoding="utf-8"))
        sectors = payload.get("sectors") if isinstance(payload, dict) else None
        if not isinstance(sectors, list):
            raise ValueError("Invalid macro_map catalog for RR RGB sync.")
        return payload

    @staticmethod
    def _extract_ontology_path(seed, project_notes):
        """Resolve ontology path for RR->RGB sync.

        Preferred source is project_notes['ontology_path']. If absent, fallback
        derives a deterministic path from the seed's IndustryGroup code by
        taking the first industry/subindustry in that group from macro_map.
        """

        notes = project_notes if isinstance(project_notes, dict) else {}
        explicit = notes.get("ontology_path") if isinstance(notes.get("ontology_path"), dict) else None
        if explicit is not None:
            required = ("sector", "subject", "industry", "subindustry")
            if all(explicit.get(key) for key in required):
                node_index = explicit.get("node_index", 0)
                return {
                    "sector": explicit["sector"],
                    "subject": explicit["subject"],
                    "industry": explicit["industry"],
                    "subindustry": explicit["subindustry"],
                    "node_index": int(node_index),
                    "source": "project_notes.ontology_path",
                }

        industry = getattr(getattr(seed, "idea", None), "industry", None)
        group = getattr(industry, "group", None)
        group_code = getattr(group, "code", None)
        if group_code is None:
            return None

        catalog = RRService._load_macro_map_catalog()
        for sector in catalog.get("sectors", []):
            for group_entry in sector.get("industry_groups", []):
                if int(group_entry.get("group_id", -1)) != int(group_code):
                    continue
                industries = group_entry.get("industries") or []
                if not industries:
                    return None
                first_industry = industries[0]
                subs = first_industry.get("sub_industries") or []
                if not subs:
                    return None
                return {
                    "sector": sector.get("sector_name"),
                    "subject": group_entry.get("subject_name"),
                    "industry": first_industry.get("industry_name"),
                    "subindustry": subs[0],
                    "node_index": 0,
                    "source": "macro_map.group_fallback",
                }
        return None

    @staticmethod
    def _sync_business_rgb_identity(seed, business, project_notes):
        """Persist RR color identity fields from ontology path via engine truth."""

        from platform_semantic.services import encode_ontology_path  # deferred import

        ontology_path = RRService._extract_ontology_path(seed, project_notes)
        if ontology_path is None:
            return None

        payload = encode_ontology_path(
            sector=ontology_path["sector"],
            subject=ontology_path["subject"],
            industry=ontology_path["industry"],
            subindustry=ontology_path["subindustry"],
            node_index=int(ontology_path.get("node_index", 0)),
        )

        display_rgb = payload["display_rgb"]
        business.color_code = payload["color_code"]
        business.compartment_id = payload["compartment_id"]
        business.display_rgb = {
            "r": int(display_rgb[0]),
            "g": int(display_rgb[1]),
            "b": int(display_rgb[2]),
        }

        notes = dict(business.project_notes or {})
        notes["rr_rgb_sync"] = {
            "source": ontology_path["source"],
            "sector": ontology_path["sector"],
            "subject": ontology_path["subject"],
            "industry": ontology_path["industry"],
            "subindustry": ontology_path["subindustry"],
            "node_index": int(ontology_path.get("node_index", 0)),
            "color_code": int(payload["color_code"]),
            "compartment_id": int(payload["compartment_id"]),
        }
        business.project_notes = notes
        business.save(update_fields=["color_code", "compartment_id", "display_rgb", "project_notes", "updated_at"])
        return payload

    @staticmethod
    def verify_business_color_integrity(business):
        """Recompute RGB identity and compare against persisted business fields."""

        sync = business.project_notes.get("rr_rgb_sync") if isinstance(business.project_notes, dict) else None
        if not isinstance(sync, dict):
            return {"status": "unavailable", "reason": "rr_rgb_sync metadata missing"}

        from platform_semantic.services import encode_ontology_path  # deferred import

        expected = encode_ontology_path(
            sector=sync["sector"],
            subject=sync["subject"],
            industry=sync["industry"],
            subindustry=sync["subindustry"],
            node_index=int(sync.get("node_index", 0)),
        )

        stored_color_code = int(business.color_code) if business.color_code is not None else -1
        stored_compartment_id = int(business.compartment_id) if business.compartment_id is not None else -1
        is_match = (
            stored_color_code == int(expected["color_code"])
            and stored_compartment_id == int(expected["compartment_id"])
        )
        return {
            "status": "ok" if is_match else "mismatch",
            "stored": {
                "color_code": business.color_code,
                "compartment_id": business.compartment_id,
                "display_rgb": business.display_rgb,
            },
            "expected": {
                "color_code": expected["color_code"],
                "compartment_id": expected["compartment_id"],
                "display_rgb": {
                    "r": int(expected["display_rgb"][0]),
                    "g": int(expected["display_rgb"][1]),
                    "b": int(expected["display_rgb"][2]),
                },
            },
        }

    @staticmethod
    def can_invoke(pip_state):
        """RR unlocks at CCPP tier or higher, in a forward-looking Convection slot (see pip_state.rr_allowed_now)."""
        return pip_state.rr_allowed_now

    @staticmethod
    def promote_seed_to_project(pip_state, seed, brand_name, market_status="draft", metadata=None, project_notes=None):
        """
        Promote a seeds.Seed to a seeds.Business ("Project"), gated at CCPP tier
        plus a forward-looking Convection slot, and validated against the
        user's SRL compartment (capacity/time_frame/tags).
        """
        from seeds.models import Business  # deferred: avoid circular import

        if not RRService.can_invoke(pip_state):
            raise RRAccessDeniedError(
                f"RR requires CCPP+ tier and a present_future/future Convection slot; "
                f"current tier={pip_state.final_tier}, time_frame={pip_state.time_slot_time_frame}."
            )

        if pip_state.territory is not None:
            validation = PIPSRLValidator.validate(
                compartment_id=pip_state.territory.index,
                raw_content=seed.idea.raw_content,
                metadata=metadata,
            )
            if validation["status"] != "approved":
                raise RRAccessDeniedError(f"SRL validation failed: {validation.get('reason')}")

        business, _ = Business.objects.update_or_create(
            seed=seed,
            defaults={
                "brand_name": brand_name,
                "market_status": market_status,
                "project_notes": project_notes or {},
            },
        )
        RRService._sync_business_rgb_identity(seed=seed, business=business, project_notes=project_notes)
        seed.idea.status = "PROJECT"
        seed.idea.save(update_fields=["status", "updated_at"])
        return business

    @staticmethod
    def promote_project_to_enterprise(pip_state, business):
        """Project -> Enterprise promotion. Deferred to Phase 4 (ENTERPRISE state doesn't exist yet)."""
        raise NotImplementedError("Project -> Enterprise promotion is implemented in Phase 4.")
