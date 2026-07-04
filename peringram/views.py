from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .models import (
    BaseTrueSquareRootMap,
    ConvectionCompartment,
    Industry,
    IndustryGroup,
    LatticeCompartment,
    RecycleThreeAllocation,
    SubIndustry,
)


GROUP_DOMAIN_ORDER = [
    "Math",
    "Language",
    "Arts",
    "Science",
    "General Information",
    "Literature",
    "Crafts",
    "Technology",
    "History",
    "Geology",
    "Policy and Governance",
    "Infrastructure Systems",
    "Operations and Logistics",
    "Quality and Safety",
    "Innovation and Optimization",
    "Cross-Sector Integration (ISEA)",
]

INDUSTRY_SLOT_LABELS = ["Foundation", "Development", "Operations", "Optimization"]
SUB_INDUSTRY_SLOT_LABELS = ["Track A", "Track B", "Track C", "Track D"]


def seed_peringram_structure():
    IndustryGroup.objects.filter(code__gt=16).delete()
    Industry.objects.filter(code__gt=4).delete()
    SubIndustry.objects.exclude(code__in=[1, 2, 3, 4]).delete()

    for group_code in range(1, 17):
        sector = IndustryGroup.sector_for_group_code(group_code)
        group_name = GROUP_DOMAIN_ORDER[group_code - 1]
        group, _ = IndustryGroup.objects.get_or_create(
            code=group_code,
            defaults={
                "sector": sector,
                "name": group_name,
                "description": f"Domain group {group_code}: {group_name}.",
            },
        )
        updates = []
        if group.sector != sector:
            group.sector = sector
            updates.append("sector")
        if group.name != group_name:
            group.name = group_name
            updates.append("name")
        if group.description != f"Domain group {group_code}: {group_name}.":
            group.description = f"Domain group {group_code}: {group_name}."
            updates.append("description")
        if updates:
            group.save(update_fields=updates)

        for industry_code in range(1, 5):
            industry_name = f"{group_name} - {INDUSTRY_SLOT_LABELS[industry_code - 1]}"
            industry, _ = Industry.objects.get_or_create(
                group=group,
                code=industry_code,
                defaults={
                    "name": industry_name,
                    "description": "Candidate industry branch within the PIP sector map.",
                },
            )
            if industry.name != industry_name:
                industry.name = industry_name
                industry.save(update_fields=["name"])
            for sub_code in range(1, 5):
                sub_name = f"{industry_name} - {SUB_INDUSTRY_SLOT_LABELS[sub_code - 1]}"
                SubIndustry.objects.get_or_create(
                    industry=industry,
                    code=sub_code,
                    defaults={
                        "name": sub_name,
                        "description": "Candidate sub-industry slot in the PIP taxonomy.",
                    },
                )

    for hour in range(24):
        index = hour + 1
        ConvectionCompartment.objects.get_or_create(
            compartment_index=index,
            defaults={
                "world_clock_hour": hour,
                "label": f"Compartment {index}",
                "lattice_coordinate": f"R{index}",
                "notes": "Convection cycle compartment on the square root lattice.",
            },
        )


class PIPView(LoginRequiredMixin, TemplateView):
    template_name = "peringram/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        seed_peringram_structure()

        recycle, _ = RecycleThreeAllocation.objects.get_or_create(user=self.request.user)
        if recycle.isea_gdp_optimization == Decimal("0.00"):
            recycle.isea_gdp_optimization = Decimal("0.01")
            recycle.save(update_fields=["isea_gdp_optimization", "updated_at"])
        user_map, _ = BaseTrueSquareRootMap.objects.get_or_create(
            user=self.request.user,
            territory_name="Default Territory",
            defaults={
                "lattice_notes": "Territory mapped on the Base True Square Root Lattice.",
            },
        )

        context["recycle"] = recycle
        context["user_map"] = user_map
        context["groups_count"] = IndustryGroup.objects.count()
        context["industries_count"] = Industry.objects.count()
        context["sub_industries_count"] = SubIndustry.objects.count()
        context["convection_count"] = ConvectionCompartment.objects.count()
        context["lattice_count"] = LatticeCompartment.objects.count()
        context["lattice_compartments"] = LatticeCompartment.objects.all()
        context["sector_groups"] = IndustryGroup.objects.all()
        return context

# Recycle 3.
class RecycleThreeView(PIPView):
    pass

# Maps
class MapsView(PIPView):
    pass

# Sectors
class SectorsView(PIPView):
    pass

# Convection cycle
class ConvectionCycleView(PIPView):
    pass
