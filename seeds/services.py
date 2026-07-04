from django.core.exceptions import ValidationError
from django.utils import timezone
import re

from peringram.models import LatticeCompartment

from .models import Idea, Seed


class RawToSeedPolishService:
    """Validates and materializes seed metadata when an idea is promoted."""

    def __init__(self, idea):
        self.idea = idea

    def validate_transition(self):
        if not self.idea.raw_content or not self.idea.raw_content.strip():
            raise ValidationError({"raw_content": "Cannot promote an empty idea to SEED."})
        if self.idea.industry_id is None:
            raise ValidationError({"industry": "Industry is required before moving to SEED."})

    def _industry_specific_requirements(self):
        industry_name = (self.idea.industry.name or "").lower()
        if "food" in industry_name:
            return ["recipe", "sourcing plan", "safety constraints"]
        if "fintech" in industry_name or "finance" in industry_name:
            return ["compliance checklist", "risk model", "audit trail"]
        return ["problem statement", "target user", "success metric"]

    def build_polish_notes(self):
        return {
            "industry": {
                "group_code": self.idea.industry.group.code,
                "industry_code": self.idea.industry.code,
                "name": self.idea.industry.name,
            },
            "requirements": self._industry_specific_requirements(),
            "notes": [],
            "promoted_at": timezone.now().isoformat(),
        }

    def run(self):
        self.validate_transition()
        defaults = {
            "polish_notes": self.build_polish_notes(),
            "germination_date": timezone.localdate(),
        }
        seed, _ = Seed.objects.update_or_create(idea=self.idea, defaults=defaults)
        return seed


def validate_idea_submission(compartment_id, raw_content, metadata=None):
    """Validate idea payloads against DB-backed lattice constraints."""
    metadata = metadata or {}
    compartment = LatticeCompartment.objects.filter(index=compartment_id).first()
    if compartment is None:
        raise ValidationError({"compartment_id": "Invalid lattice compartment."})

    content_length = len((raw_content or "").strip())
    if content_length == 0:
        raise ValidationError({"raw_content": "Idea content cannot be empty."})

    if content_length > compartment.capacity:
        return {
            "status": "rejected",
            "reason": "Content exceeds compartment capacity.",
            "capacity": compartment.capacity,
            "content_length": content_length,
            "category": compartment.category,
        }

    tags = set(metadata.get("tags", []))
    if compartment.time_frame == LatticeCompartment.TIME_PAST and "historical" not in tags:
        return {
            "status": "rejected",
            "reason": "Past compartment requires a 'historical' tag.",
            "category": compartment.category,
        }
    if compartment.time_frame == LatticeCompartment.TIME_FUTURE and "forecast" not in tags:
        return {
            "status": "rejected",
            "reason": "Future compartment requires a 'forecast' tag.",
            "category": compartment.category,
        }

    return {
        "status": "approved",
        "category": compartment.category,
        "time_frame": compartment.get_time_frame_display(),
        "capacity": compartment.capacity,
        "compartment_index": compartment.index,
    }


class LatticeCompartmentValidationService:
    """Reusable template service for compartment-scoped feature validators."""

    def __init__(self, compartment_id):
        self.compartment_id = compartment_id

    def validate(self, raw_content, metadata=None):
        return validate_idea_submission(self.compartment_id, raw_content, metadata=metadata)


def _tokenize(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _jaccard(a_tokens, b_tokens):
    if not a_tokens or not b_tokens:
        return 0.0
    overlap = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return overlap / union if union else 0.0


def find_similar_ideas(raw_content, industry_id=None, limit=5, exclude_idea_id=None):
    """Return likely related idea IDs using lightweight token overlap scoring."""
    source_tokens = _tokenize(raw_content)
    queryset = Idea.objects.all()
    if industry_id is not None:
        queryset = queryset.filter(industry_id=industry_id)
    if exclude_idea_id is not None:
        queryset = queryset.exclude(id=exclude_idea_id)

    candidates = []
    for idea in queryset.only("id", "raw_content")[:300]:
        score = _jaccard(source_tokens, _tokenize(idea.raw_content))
        if score > 0:
            candidates.append({"idea_id": idea.id, "similarity": round(score, 4)})

    candidates.sort(key=lambda item: item["similarity"], reverse=True)
    return candidates[:limit]