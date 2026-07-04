from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from platform_core.models import MLASClassificationRecord


class Command(BaseCommand):
    help = "Seed 20 reviewed MLAS starter classification records (idempotent)."

    def handle(self, *args, **options):
        user_model = get_user_model()
        reviewer, _ = user_model.objects.get_or_create(
            username="classification_seed_reviewer",
            defaults={
                "email": "classification_seed_reviewer@example.com",
                "is_staff": True,
            },
        )
        if not reviewer.is_staff:
            reviewer.is_staff = True
            reviewer.save(update_fields=["is_staff"])

        subjects = ["MATH", "LANG", "ARTS", "SCI"]
        branches = ["SACP", "EDNP", "VLSM", "MBSP"]

        created = 0
        updated = 0

        for index in range(1, 21):
            subject = subjects[(index - 1) % len(subjects)]
            branch = branches[(index - 1) % len(branches)]
            term_code = f"T{index:03d}"
            record_id = f"STARTER-MLAS-{index:03d}"

            payload = {
                "source_name_raw": f"Starter Industry {index}",
                "source_description_raw": f"Starter reviewed row {index} for Basetrue/MLAS governance.",
                "target_layer": MLASClassificationRecord.TARGET_TERM,
                "mlas_subject_code": subject,
                "mlas_branch_code": branch,
                "mlas_term_code": term_code,
                "mlas_meta_term_code": "",
                "dewey_code": str(600 + index),
                "gics_sector_code": f"{10 + ((index - 1) % 6):02d}",
                "gics_industry_group_code": f"{1000 + index}",
                "gics_industry_code": f"{100000 + index}",
                "gics_sub_industry_code": f"{10101000 + index}",
                "naics_code_2": f"{11 + ((index - 1) % 8):02d}",
                "naics_code_3": f"{111 + ((index - 1) % 8):03d}",
                "naics_code_4": f"{1110 + ((index - 1) % 8):04d}",
                "naics_code_5": f"{11100 + ((index - 1) % 8):05d}",
                "naics_code_6": f"{111000 + index:06d}",
                "algorithm_1_score": 0.86,
                "algorithm_2_score": 0.82,
                "algorithm_3_score": 0.88,
                "algorithm_4_score": 0.84,
                "quadrant_slug": "bos",
                "basetrue_label": f"Basetrue Starter {index}",
                "basetrue_description": f"Basetrue starter industry profile {index}.",
                "confidence_overall": 0.83,
                "confidence_reason": "Seeded starter row with reviewed alignment.",
                "review_status": MLASClassificationRecord.REVIEW_APPROVED,
                "reviewer": reviewer,
                "reviewed_at": timezone.now(),
                "notes": "Seeded by management command seed_mlas_starter_records.",
            }

            record, is_created = MLASClassificationRecord.objects.get_or_create(
                record_id=record_id,
                defaults=payload,
            )
            if is_created:
                created += 1
            else:
                for field_name, field_value in payload.items():
                    setattr(record, field_name, field_value)
                record.save()
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Starter seed complete: created={created}, updated={updated}"))
