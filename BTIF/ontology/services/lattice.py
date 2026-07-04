from dataclasses import asdict, dataclass

from ontology.models import SubIndustry, TemporalSlot


@dataclass(frozen=True)
class LatticeNode:
    subject: str
    branch: str
    industry: str
    sub_industry: str
    sub_industry_order: int
    position: int
    tense: str
    color: str
    phase: str


def build_lattice_nodes():
    slots = list(TemporalSlot.objects.order_by("position"))
    if not slots:
        return []

    nodes = []
    for idx, sub in enumerate(
        SubIndustry.objects.select_related("industry__branch__subject")
        .order_by(
            "industry__branch__subject__order",
            "industry__branch__order",
            "industry__order",
            "order",
        )
    ):
        slot = slots[idx % len(slots)]
        node = LatticeNode(
            subject=sub.industry.branch.subject.name,
            branch=sub.industry.branch.name,
            industry=sub.industry.name,
            sub_industry=sub.name,
            sub_industry_order=sub.order,
            position=slot.position,
            tense=slot.tense,
            color=slot.color,
            phase=slot.default_phase,
        )
        nodes.append(asdict(node))

    return nodes