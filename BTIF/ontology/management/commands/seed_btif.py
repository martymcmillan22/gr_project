from django.core.management.base import BaseCommand
from django.db import transaction

from ontology.models import Branch, Industry, Subject, SubIndustry, TemporalSlot


BTIF_STRUCTURE = [
    {
        "subject": {"name": "Math", "acronym": "MATH", "order": 1},
        "branch_group_acronym": "SACP",
        "branches": [
            {
                "name": "Statistics",
                "industries": [
                    "Predictive Analytics",
                    "Data Quality Systems",
                    "Sampling & Survey Engineering",
                    "Statistical Automation Platforms",
                ],
            },
            {
                "name": "Algebra",
                "industries": [
                    "Symbolic Computation Systems",
                    "Equation Modeling Platforms",
                    "Constraint-Solving Engines",
                    "Algebraic Data Structures",
                ],
            },
            {
                "name": "Calculus",
                "industries": [
                    "Optimization & Gradient Systems",
                    "Dynamic Systems Modeling",
                    "Rate-of-Change Analytics",
                    "Continuous Simulation Engines",
                ],
            },
            {
                "name": "Probability",
                "industries": [
                    "Stochastic Modeling",
                    "Risk & Uncertainty Systems",
                    "Random Process Engineering",
                    "Probabilistic AI Platforms",
                ],
            },
        ],
    },
    {
        "subject": {"name": "Language", "acronym": "LANG", "order": 2},
        "branch_group_acronym": "EDNP",
        "branches": [
            {
                "name": "Expository",
                "industries": [
                    "Technical Documentation Systems",
                    "Knowledge Base Engineering",
                    "Instructional Design Platforms",
                    "Information Structuring Engines",
                ],
            },
            {
                "name": "Descriptive",
                "industries": [
                    "Metadata & Tagging Systems",
                    "Descriptive Analytics",
                    "Content Profiling Engines",
                    "Semantic Annotation Platforms",
                ],
            },
            {
                "name": "Narrative",
                "industries": [
                    "Story Architecture Systems",
                    "Narrative AI Engines",
                    "Interactive Plot Design",
                    "Sequential Content Modeling",
                ],
            },
            {
                "name": "Persuasive",
                "industries": [
                    "Behavioral Influence Systems",
                    "Marketing Logic Engines",
                    "Decision-Shaping Platforms",
                    "Rhetorical AI Systems",
                ],
            },
        ],
    },
    {
        "subject": {"name": "Arts", "acronym": "ARTS", "order": 3},
        "branch_group_acronym": "VLSM",
        "branches": [
            {
                "name": "Visual",
                "industries": [
                    "Visual Intelligence Systems",
                    "Design Automation Engines",
                    "Image Interpretation Platforms",
                    "Visual Asset Management",
                ],
            },
            {
                "name": "Literature",
                "industries": [
                    "Textual Analysis Systems",
                    "Literary Structure Engines",
                    "Content Generation Platforms",
                    "Digital Publishing Systems",
                ],
            },
            {
                "name": "Sculpture",
                "industries": [
                    "3D Modeling Systems",
                    "Material Simulation Engines",
                    "Spatial Fabrication Platforms",
                    "Structural Aesthetic Systems",
                ],
            },
            {
                "name": "Music",
                "industries": [
                    "Audio Intelligence Systems",
                    "Generative Music Engines",
                    "Sound Design Platforms",
                    "Acoustic Modeling Systems",
                ],
            },
        ],
    },
    {
        "subject": {"name": "Science", "acronym": "SCIE", "order": 4},
        "branch_group_acronym": "MBSP",
        "branches": [
            {
                "name": "Math Logic",
                "industries": [
                    "Logic Automation Systems",
                    "Inference Engines",
                    "Formal Verification Platforms",
                    "Computational Reasoning Systems",
                ],
            },
            {
                "name": "Biology",
                "industries": [
                    "Bioinformatics Systems",
                    "Genomic Modeling Engines",
                    "Biological Simulation Platforms",
                    "Life-System Analytics",
                ],
            },
            {
                "name": "Social",
                "industries": [
                    "Social Dynamics Modeling",
                    "Population Behavior Systems",
                    "Cultural Pattern Engines",
                    "Community Intelligence Platforms",
                ],
            },
            {
                "name": "Physical",
                "industries": [
                    "Physics Simulation Engines",
                    "Energy Systems Modeling",
                    "Material Physics Platforms",
                    "Environmental Dynamics Systems",
                ],
            },
        ],
    },
]

TEMPORAL_SLOTS = {
    1: ("past", "red"),
    2: ("present_past", "blue"),
    3: ("present_future", "yellow"),
    4: ("future", "green"),
    5: ("past", "purple"),
    6: ("present_past", "teal"),
    7: ("present_future", "orange"),
    8: ("future", "lime"),
    9: ("past", "pink"),
    10: ("present_past", "cyan"),
    11: ("present_future", "amber"),
    12: ("future", "green-lime"),
}


class Command(BaseCommand):
    help = "Seed canonical BTIF data (4 subjects, 16 branches, 64 industries, 256 sub-industries)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing ontology data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Resetting ontology data..."))
            TemporalSlot.objects.all().delete()
            SubIndustry.objects.all().delete()
            Industry.objects.all().delete()
            Branch.objects.all().delete()
            Subject.objects.all().delete()

        for section in BTIF_STRUCTURE:
            subject_data = section["subject"]
            subject, _ = Subject.objects.update_or_create(
                name=subject_data["name"],
                defaults={
                    "acronym": subject_data["acronym"],
                    "order": subject_data["order"],
                },
            )

            for branch_idx, branch_data in enumerate(section["branches"], start=1):
                branch, _ = Branch.objects.update_or_create(
                    subject=subject,
                    name=branch_data["name"],
                    defaults={
                        "acronym": section["branch_group_acronym"],
                        "order": branch_idx,
                    },
                )

                for industry_idx, industry_name in enumerate(branch_data["industries"], start=1):
                    industry, _ = Industry.objects.update_or_create(
                        branch=branch,
                        name=industry_name,
                        defaults={"order": industry_idx},
                    )

                    for sub_idx in range(1, 5):
                        SubIndustry.objects.update_or_create(
                            industry=industry,
                            order=sub_idx,
                            defaults={"name": f"{industry_name} Sub {sub_idx}"},
                        )

        for position, (tense, color) in TEMPORAL_SLOTS.items():
            TemporalSlot.objects.update_or_create(
                position=position,
                defaults={"tense": tense, "color": color},
            )

        self.stdout.write(self.style.SUCCESS("BTIF ontology seed complete."))
        self.stdout.write(
            f"Subjects: {Subject.objects.count()}, "
            f"Branches: {Branch.objects.count()}, "
            f"Industries: {Industry.objects.count()}, "
            f"Sub-industries: {SubIndustry.objects.count()}, "
            f"Temporal slots: {TemporalSlot.objects.count()}"
        )